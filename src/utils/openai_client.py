import os
import openai
from typing import Dict, List, Optional

class OpenAIClient:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def generate_response(self, lead_data: Dict, incoming_message: str, missing_fields: List[str], needs_tour_availability: bool = False, missing_optional: Optional[List[str]] = None) -> str:
        """Generate a conversational response based on lead data and missing fields"""
        
        if missing_optional is None:
            missing_optional = []
        
        # Build simple list of what we have vs don't have for REQUIRED fields
        database_status = []
        required_fields = ["move_in_date", "price", "beds", "baths", "location", "amenities"]
        
        for field in required_fields:
            value = lead_data.get(field)
            has_content = value and str(value).strip()
            status = "✓ HAS DATA" if has_content else "✗ MISSING"
            database_status.append(f"{field}: {status} ({value if has_content else 'empty'})")
        
        # Add optional fields status
        optional_fields = ["rental_urgency", "boston_rental_experience"]
        database_status.append("\nOPTIONAL FIELDS:")
        for field in optional_fields:
            value = lead_data.get(field)
            has_content = value and str(value).strip()
            status = "✓ HAS DATA" if has_content else "○ OPTIONAL"
            database_status.append(f"{field}: {status} ({value if has_content else 'could ask about'})")
        
        database_status_str = "\n".join(database_status)
        
        # Include chat history for better conversational context
        chat_history = lead_data.get("chat_history", "")
        if chat_history:
            # Limit to last 10 messages to avoid token limits
            chat_lines = chat_history.strip().split('\n')
            if len(chat_lines) > 10:
                chat_lines = chat_lines[-10:]
            chat_history_str = "\n".join(chat_lines)
        else:
            chat_history_str = "No conversation history yet"
        
        if needs_tour_availability:
            phase = "TOUR_SCHEDULING"
            phase_instructions = """All qualification info is complete. Ask ONLY about tour availability - when they're available for property tours. Don't ask about anything else."""
        elif missing_fields:
            phase = "QUALIFICATION"
            missing_fields_str = ", ".join(missing_fields)
            phase_instructions = f"""

                Still missing REQUIRED: {missing_fields_str}

                Before asking anything:
                1. Check the database status above - only ask about "✗ MISSING" fields
                2. Check conversation history - don't repeat questions

                Ask 2-3 questions about missing required fields only:
                - Bedrooms + bathrooms together
                - Price + location together  
                - Move-in date + amenities together

                For amenities, suggest: in-unit laundry, central air, parking, gym, dishwasher, balcony, pet-friendly.

                """
        elif missing_optional and len(missing_optional) > 0:
            phase = "OPTIONAL_QUESTIONS"
            missing_optional_str = ", ".join(missing_optional)
            phase_instructions = f"""
                All required info is complete! You can ask 1-2 optional questions to gather extra helpful info: {missing_optional_str}

                Optional questions:
                - rental_urgency: "How quickly are you looking to move? Are you hoping to find something within the next few weeks, or do you have more flexibility with timing?"
                - boston_rental_experience: "Do you mind if I ask - have you rented an apartment in Boston before, or is this your first rental experience here? I can give you a brief overview of the process if helpful."

                Ask naturally, don't force it. If conversation doesn't flow naturally, skip to asking about tour availability.
                
                """
        else:
            phase = "COMPLETE"
            phase_instructions = """All information is collected! Send a professional completion message letting them know your teammate will contact them directly to schedule their tour. This ends the qualification conversation."""
        
        system_prompt = f"""
            You are a professional assistant helping a busy real estate agent qualify leads over SMS. You are efficient, helpful, and direct. You are part of a group chat with the lead and the agent.

            CURRENT PHASE: {phase}

            === CONVERSATION HISTORY ===
            {chat_history_str}

            === DATABASE STATUS ===
            {database_status_str}

            === CRITICAL RULES ===
            1. NEVER ask about fields marked "✓ HAS DATA" above - we already have this information.
            2. ONLY ask about what the current phase requires.
            3. Don't ask multiple questions when one will do.

            {phase_instructions}

            Guidelines:
            - Keep responses concise and professional (SMS-appropriate)
            - Be direct and efficient - you handle many leads daily
            - NEVER ask about information we already have (see above section)
            - Ask 2-3 questions per message when in qualification phase
            - Acknowledge their responses briefly before asking new questions
            - No emojis - maintain professional tone
            - For amenities, suggest examples: in-unit laundry, central air, parking, gym, dishwasher, balcony, pet-friendly.

            The lead just sent: "{incoming_message}"
            
            """

        user_prompt = f"""
            Generate a professional, efficient response based on the current phase and what we still need to collect. Bundle questions logically when possible.
                """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.5
            )
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("OpenAI returned None content")

            return content.strip()
        
        except Exception as e:
            print(f"Error generating OpenAI response: {e}")
            return "Thanks for your message. Our agent will follow up with you soon."
    
    def extract_lead_info(self, message: str, current_data: Dict) -> Dict:
        """Extract any qualification information from the message"""
        
        system_prompt = f"""
            You are an expert at extracting real estate information from SMS messages. You must be very thorough and catch ALL information provided.

            CURRENT LEAD DATA (do NOT extract if already filled):
            Move-in date: {current_data.get('move_in_date', 'EMPTY')}
            Price range: {current_data.get('price', 'EMPTY')}
            Bedrooms: {current_data.get('beds', 'EMPTY')}
            Bathrooms: {current_data.get('baths', 'EMPTY')}
            Location: {current_data.get('location', 'EMPTY')}
            Amenities: {current_data.get('amenities', 'EMPTY')}
            Tour availability: {current_data.get('tour_availability', 'EMPTY')}
            Rental urgency: {current_data.get('rental_urgency', 'EMPTY')}
            Boston rental experience: {current_data.get('boston_rental_experience', 'EMPTY')}

            EXTRACT ALL NEW INFORMATION from this message: "{message}"

            Look for these patterns:
            - Move-in date: "september 1st", "Sept 1", "9/1", "next month", "ASAP", etc.
            - Price: "$1500", "1500/mo", "$2000 max", "under 2k", "budget is", etc.  
            - Bedrooms: "5 bed", "5 bedroom", "5br", "five bedroom", etc.
            - Bathrooms: "2 bath", "2 bathroom", "2ba", "two bath", etc.
            - Location: "mission hill", "downtown", "near", "in", neighborhood names, etc.
            - Amenities: "parking", "laundry", "none", "no amenities", specific features, etc.
            - Tour availability: "weekends", "available", "free", specific days/times, etc.
            - Rental urgency: "ASAP", "quickly", "few weeks", "flexible", "no rush", etc.
            - Boston rental experience: "first time", "never rented", "familiar", "rented before", etc.

            CRITICAL: Extract information even if mentioned casually. Be aggressive in extraction.

            Return ONLY a JSON object with the NEW information found. Use these exact field names:
            - move_in_date  
            - price
            - beds  
            - baths
            - location
            - amenities
            - tour_availability
            - rental_urgency
            - boston_rental_experience

            EXAMPLES:
            Message: "I need a place for september 1st, 2025, looking for a 5 bed, 2 bath, 1500/mo, on mission hill please"
            Response: {{"move_in_date": "september 1st, 2025", "beds": "5", "baths": "2", "price": "1500/mo", "location": "mission hill"}}

            Message: "I need something ASAP, this is my first time renting in Boston"
            Response: {{"rental_urgency": "ASAP", "boston_rental_experience": "first time renting in Boston"}}

            Message: "I'm flexible with timing, I've rented here before"
            Response: {{"rental_urgency": "flexible", "boston_rental_experience": "rented here before"}}

            If NO new information found, return: {{}}"
            
            """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract ALL information from: {message}"}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            import json
            result_text = response.choices[0].message.content
            if result_text is None:
                raise ValueError("OpenAI returned None content")
            result_text = result_text.strip()
            print(f"[DEBUG] Extract attempt for message '{message}': {result_text}")
            
            extracted_info = json.loads(result_text)
            print(f"[DEBUG] Successfully extracted: {extracted_info}")
            return extracted_info
        
        except Exception as e:
            print(f"[ERROR] Failed to extract lead info from '{message}': {e}")
            return {} 
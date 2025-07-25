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
    
    def generate_response(self, lead_data: Dict, incoming_message: str, missing_fields: List[str], needs_tour_availability: bool = False) -> str:
        """Generate a conversational response based on lead data and missing fields"""
        
        # Build context about what we know
        known_info = []
        if lead_data.get("move_in_date"):
            known_info.append(f"Move-in date: {lead_data['move_in_date']}")
        if lead_data.get("price"):
            known_info.append(f"Price range: {lead_data['price']}")
        if lead_data.get("beds"):
            known_info.append(f"Bedrooms: {lead_data['beds']}")
        if lead_data.get("baths"):
            known_info.append(f"Bathrooms: {lead_data['baths']}")
        if lead_data.get("location"):
            known_info.append(f"Location: {lead_data['location']}")
        if lead_data.get("amenities"):
            known_info.append(f"Amenities: {lead_data['amenities']}")
        if lead_data.get("tour_availability"):
            known_info.append(f"Tour availability: {lead_data['tour_availability']}")
        
        known_info_str = "\n".join(known_info) if known_info else "No information collected yet"
        
        # Create explicit list of fields that have ANY content (even partial)
        fields_with_content = []
        qualification_fields = ["move_in_date", "price", "beds", "baths", "location", "amenities"]
        for field in qualification_fields:
            value = lead_data.get(field)
            if value and str(value).strip():  # Any non-empty content
                fields_with_content.append(field)
        
        fields_with_content_str = ", ".join(fields_with_content) if fields_with_content else "none"
        
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
            phase_instructions = """We have all the qualification information. Now ask for their tour availability - when they'd be available to tour properties. Be specific about asking for days/times."""
        elif missing_fields:
            phase = "QUALIFICATION"
            missing_fields_str = ", ".join(missing_fields)
            phase_instructions = f"""We still need: {missing_fields_str}. 

🚨 CRITICAL ANTI-REPETITION CHECK 🚨
Before asking ANYTHING, you MUST carefully read the entire conversation history above. If you see that you have ALREADY asked about any of these missing fields in previous messages, DO NOT ask about them again - even if the lead didn't answer or gave an unclear answer.

🚨 DOUBLE-CHECK AGAINST FIELDS WITH CONTENT 🚨
NEVER ask about any field listed in "FIELDS WITH ANY CONTENT" above. If a field has ANY data (even partial like "ac" for amenities), DO NOT ask about it.

ANALYSIS REQUIRED: For each missing field ({missing_fields_str}), check:
1. Is this field in the "FIELDS WITH ANY CONTENT" list? If YES, don't ask about it.
2. Have I already asked about this field in the conversation history? If YES, don't ask again.
3. Only ask about fields that are BOTH missing AND have no content AND haven't been asked about.

ONLY ask about missing fields that:
- Have NO content in the database 
- Have NOT been asked about in conversation history
- Are truly empty/null

Bundle 2-3 NEW (never asked before, no content) questions logically:
- Bundle: bedrooms + bathrooms ("How many bedrooms and bathrooms are you looking for?")
- Bundle: price + location ("What's your budget and preferred neighborhoods?")  
- Bundle: move-in date + amenities ("When do you need to move in, and any specific amenities you want?")

For amenities, suggest examples: in-unit laundry, central air, parking, gym, pool, dishwasher, balcony, pet-friendly."""
        else:
            phase = "COMPLETE"
            phase_instructions = """All information is collected! Send a professional completion message letting them know our manager will contact them directly to schedule their tour. This ends the qualification conversation."""
        
        system_prompt = f"""You are a professional assistant helping a busy real estate agent qualify leads over SMS. You are efficient, helpful, and direct. You are part of a group chat with the lead and the agent.

CURRENT PHASE: {phase}

=== CONVERSATION HISTORY ===
{chat_history_str}

=== INFORMATION WE ALREADY HAVE ===
{known_info_str}

=== FIELDS WITH ANY CONTENT (NEVER ASK ABOUT THESE) ===
Fields that have ANY data (even partial): {fields_with_content_str}

=== CRITICAL RULES ===
1. DO NOT ask about any information listed in "INFORMATION WE ALREADY HAVE" - we have this data stored.
2. NEVER EVER ask about any fields listed in "FIELDS WITH ANY CONTENT" - even if the data seems incomplete, if we have ANY content for a field, don't ask about it again.
3. DO NOT repeat questions you've already asked in the conversation history - even if the lead hasn't answered yet.
4. Carefully analyze the conversation history to see what you've already asked about before formulating new questions.
5. If you've already asked about a missing field, acknowledge their response or gently follow up - don't re-ask the same question.

{phase_instructions}

Guidelines:
- Keep responses concise and professional (SMS-appropriate)
- Be direct and efficient - you handle many leads daily
- NEVER ask about information we already have (see above section)
- Ask 2-3 questions per message when in qualification phase
- Acknowledge their responses briefly before asking new questions
- No emojis - maintain professional tone
- For amenities, suggest examples: in-unit laundry, central air, parking, gym, pool, dishwasher, balcony, pet-friendly

The lead just sent: "{incoming_message}"
"""

        user_prompt = f"""Generate a professional, efficient response based on the current phase and what we still need to collect. Bundle questions logically when possible."""

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
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generating OpenAI response: {e}")
            return "Thanks for your message. Our agent will follow up with you soon."
    
    def extract_lead_info(self, message: str, current_data: Dict) -> Dict:
        """Extract any qualification information from the message"""
        
        system_prompt = f"""You are an expert at extracting real estate information from SMS messages. You must be very thorough and catch ALL information provided.

CURRENT LEAD DATA (do NOT extract if already filled):
Move-in date: {current_data.get('move_in_date', 'EMPTY')}
Price range: {current_data.get('price', 'EMPTY')}
Bedrooms: {current_data.get('beds', 'EMPTY')}
Bathrooms: {current_data.get('baths', 'EMPTY')}
Location: {current_data.get('location', 'EMPTY')}
Amenities: {current_data.get('amenities', 'EMPTY')}
Tour availability: {current_data.get('tour_availability', 'EMPTY')}

EXTRACT ALL NEW INFORMATION from this message: "{message}"

Look for these patterns:
- Move-in date: "september 1st", "Sept 1", "9/1", "next month", "ASAP", etc.
- Price: "$1500", "1500/mo", "$2000 max", "under 2k", "budget is", etc.  
- Bedrooms: "5 bed", "5 bedroom", "5br", "five bedroom", etc.
- Bathrooms: "2 bath", "2 bathroom", "2ba", "two bath", etc.
- Location: "mission hill", "downtown", "near", "in", neighborhood names, etc.
- Amenities: "parking", "laundry", "none", "no amenities", specific features, etc.
- Tour availability: "weekends", "available", "free", specific days/times, etc.

Return ONLY a JSON object with the NEW information found. Use these exact field names:
- move_in_date  
- price
- beds  
- baths
- location
- amenities
- tour_availability

EXAMPLES:
Message: "I need a place for september 1st, 2025, looking for a 5 bed, 2 bath, 1500/mo, on mission hill please"
Response: {{"move_in_date": "september 1st, 2025", "beds": "5", "baths": "2", "price": "1500/mo", "location": "mission hill"}}

Message: "none" (when asked about amenities)
Response: {{"amenities": "none"}}

Message: "I'm looking for something under $2000 in downtown"  
Response: {{"price": "under $2000", "location": "downtown"}}

If NO new information found, return: {{}}
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
            result_text = response.choices[0].message.content.strip()
            print(f"[DEBUG] Extract attempt for message '{message}': {result_text}")
            
            extracted_info = json.loads(result_text)
            print(f"[DEBUG] Successfully extracted: {extracted_info}")
            return extracted_info
        
        except Exception as e:
            print(f"[ERROR] Failed to extract lead info from '{message}': {e}")
            return {} 
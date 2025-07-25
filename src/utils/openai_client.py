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

CRITICAL: Before asking ANY questions, carefully analyze the conversation history above to see what questions you've ALREADY ASKED about these missing fields. DO NOT repeat questions you've already asked, even if the lead hasn't answered them yet.

Only ask about missing fields that you haven't already inquired about in the conversation history. If you've already asked about a missing field, acknowledge their previous response or gently follow up, don't re-ask the same question.

Bundle 2-3 NEW questions logically:
- Bundle: bedrooms + bathrooms ("How many bedrooms and bathrooms are you looking for?")
- Bundle: price + location ("What's your budget and preferred neighborhoods?")  
- Bundle: move-in date + amenities ("When do you need to move in, and any specific amenities you want?")

For amenities, provide examples: in-unit laundry, central air, parking, gym, pool, dishwasher, balcony, pet-friendly."""
        else:
            phase = "COMPLETE"
            phase_instructions = """All information is collected! Send a professional completion message letting them know our manager will contact them directly to schedule their tour. This ends the qualification conversation."""
        
        system_prompt = f"""You are a professional assistant helping a busy real estate agent qualify leads over SMS. You are efficient, helpful, and direct. You are part of a group chat with the lead and the agent.

CURRENT PHASE: {phase}

=== CONVERSATION HISTORY ===
{chat_history_str}

=== INFORMATION WE ALREADY HAVE ===
{known_info_str}

=== CRITICAL RULES ===
1. DO NOT ask about any information listed in "INFORMATION WE ALREADY HAVE" - we have this data stored.
2. DO NOT repeat questions you've already asked in the conversation history - even if the lead hasn't answered yet.
3. Carefully analyze the conversation history to see what you've already asked about before formulating new questions.
4. If you've already asked about a missing field, acknowledge their response or gently follow up - don't re-ask the same question.

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
        
        system_prompt = f"""You are helping extract real estate lead qualification information from SMS messages.

Current lead data:
Move-in date: {current_data.get('move_in_date', '')}
Price range: {current_data.get('price', '')}
Bedrooms: {current_data.get('beds', '')}
Bathrooms: {current_data.get('baths', '')}
Location: {current_data.get('location', '')}
Amenities: {current_data.get('amenities', '')}
Tour availability: {current_data.get('tour_availability', '')}

Extract any new information from this message: "{message}"

Return a JSON object with only the fields that have new information. Use these exact field names:
- move_in_date  
- price
- beds
- baths
- location
- amenities
- tour_availability

For tour_availability, look for availability mentions like "available weekends", "free Tuesday evenings", "anytime next week", etc.

If no new information is found, return an empty JSON object: {{}}.

Examples:
Message: "I'm looking for a 2 bedroom, 2 bath place"
Response: {{"beds": "2", "baths": "2"}}

Message: "Budget is $2500 max, prefer downtown or midtown"
Response: {{"price": "$2500 max", "location": "downtown or midtown"}}

Message: "I'm free for tours on weekends"
Response: {{"tour_availability": "weekends"}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract information from: {message}"}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            import json
            extracted_info = json.loads(response.choices[0].message.content.strip())
            return extracted_info
        
        except Exception as e:
            print(f"Error extracting lead info: {e}")
            return {} 
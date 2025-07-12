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
        
        if needs_tour_availability:
            phase = "TOUR_SCHEDULING"
            phase_instructions = """We have all the qualification information. Now ask for their tour availability - when they'd be available to tour properties. Be specific about asking for days/times."""
        elif missing_fields:
            phase = "QUALIFICATION"
            missing_fields_str = ", ".join(missing_fields)
            phase_instructions = f"""We still need: {missing_fields_str}. Ask for 2-3 of these in one message, bundling them logically:
- Bundle: bedrooms + bathrooms ("How many bedrooms and bathrooms are you looking for?")
- Bundle: price + location ("What's your budget and preferred neighborhoods?")
- Bundle: move-in date + amenities ("When do you need to move in, and any specific amenities you want like in-unit laundry, central air, parking, gym, pool, etc?")
Ask multiple questions per message to be efficient.

For amenities, provide examples like: in-unit laundry, central air, parking, gym, pool, dishwasher, balcony, pet-friendly, etc."""
        else:
            phase = "COMPLETE"
            phase_instructions = """All information is collected! Let them know our agent will follow up soon to schedule a tour."""
        
        system_prompt = f"""You are a friendly AI assistant helping a real estate agent qualify leads over SMS. You are part of a group chat with the lead and the agent.

CURRENT PHASE: {phase}

=== INFORMATION WE ALREADY HAVE ===
{known_info_str}

=== CRITICAL RULE ===
DO NOT ask about any information listed above! We already have this data.

{phase_instructions}

Guidelines:
- Keep responses concise (SMS-appropriate)
- Be conversational and friendly
- NEVER EVER ask about information we already have (see above section)
- Ask 2-3 questions per message when in qualification phase
- Acknowledge their responses before asking new questions
- Use emojis sparingly but appropriately
- For amenities, suggest examples: in-unit laundry, central air, parking, gym, pool, dishwasher, balcony, pet-friendly

The lead just sent: "{incoming_message}"
"""

        user_prompt = f"""Generate a friendly response based on the current phase and what we still need to collect. Bundle questions logically when possible."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generating OpenAI response: {e}")
            return "Thanks for your message! I'll have our agent follow up with you soon."
    
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
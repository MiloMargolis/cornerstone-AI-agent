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
    
    def generate_response(self, lead_data: Dict, incoming_message: str, missing_fields: List[str]) -> str:
        """Generate a conversational response based on lead data and missing fields"""
        
        # Build context about what we know
        known_info = []
        if lead_data.get("name"):
            known_info.append(f"Name: {lead_data['name']}")
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
        
        known_info_str = "\n".join(known_info) if known_info else "No information collected yet"
        missing_fields_str = ", ".join(missing_fields) if missing_fields else "All information collected"
        
        system_prompt = f"""You are a friendly AI assistant helping a real estate agent qualify leads over SMS. You are part of a group chat with the lead and the agent.

Your role is to:
1. Have natural, friendly conversations with leads
2. Gradually collect qualification information through conversation
3. Ask follow-up questions when needed
4. Be helpful but not overly pushy

Current lead information:
{known_info_str}

Still need to collect: {missing_fields_str}

Guidelines:
- Keep responses concise (SMS-appropriate)
- Ask only one question at a time
- Be conversational and friendly
- If they provide information, acknowledge it before asking the next question
- If all information is collected, let them know you'll have the agent follow up soon
- Don't repeat questions about information you already have

The lead just sent: "{incoming_message}"
"""

        user_prompt = f"""Based on the lead's message and what information we still need, generate a friendly response that continues the conversation naturally. If we still need information, ask about one of the missing fields in a conversational way."""

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
Name: {current_data.get('name', '')}
Move-in date: {current_data.get('move_in_date', '')}
Price range: {current_data.get('price', '')}
Bedrooms: {current_data.get('beds', '')}
Bathrooms: {current_data.get('baths', '')}
Location: {current_data.get('location', '')}
Amenities: {current_data.get('amenities', '')}

Extract any new information from this message: "{message}"

Return a JSON object with only the fields that have new information. Use these exact field names:
- name
- move_in_date  
- price
- beds
- baths
- location
- amenities

If no new information is found, return an empty JSON object: {{}}.

Examples:
Message: "Hi, I'm John and I'm looking for a 2 bedroom place"
Response: {{"name": "John", "beds": "2"}}

Message: "I need something under $2000 in downtown"
Response: {{"price": "under $2000", "location": "downtown"}}
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
import os
import openai
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from services.interfaces import IAIService
from models.lead import Lead
from utils.constants import PHASE_CONFIGS, REQUIRED_FIELDS, OPTIONAL_FIELDS
from utils.prompt_loader import PromptLoader


class OpenAIService(IAIService):
    """OpenAI service implementation - migrated from legacy client"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY environment variable")

        self.client = openai.OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.prompt_loader = PromptLoader()

    def _get_database_status(self, lead_data: Dict) -> str:
        """Generate a string representing the database status of required and optional fields"""
        database_status = []

        for field in REQUIRED_FIELDS:
            value = lead_data.get(field)
            has_content = value and str(value).strip()
            status = "✓ HAS DATA" if has_content else "✗ MISSING"
            database_status.append(
                f"{field}: {status} ({value if has_content else 'empty'})"
            )

        database_status.append("\nOPTIONAL FIELDS:")
        for field in OPTIONAL_FIELDS:
            value = lead_data.get(field)
            has_content = value and str(value).strip()
            status = "✓ HAS DATA" if has_content else "○ OPTIONAL"
            database_status.append(
                f"{field}: {status} ({value if has_content else 'could ask about'})"
            )

        database_status_str = "\n".join(database_status)
        return database_status_str

    def _get_chat_history(self, lead_data: Dict) -> str:
        """Retrieve the chat history in a format suitable for the OpenAI API"""
        chat_history = lead_data.get("chat_history", "")
        if chat_history:
            # Limit to last 10 messages to avoid token limits
            chat_lines = chat_history.strip().split("\n")
            if len(chat_lines) > 10:
                chat_lines = chat_lines[-10:]
            chat_history_str = "\n".join(chat_lines)
        else:
            chat_history_str = "No conversation history yet"
        return chat_history_str

    def _get_phase_instructions(
        self,
        needs_tour_availability: bool,
        missing_fields: List[str],
        missing_optional: Optional[List[str]],
    ) -> Tuple[str, str]:
        """Determine the current phase and instructions based on the lead's data"""
        if needs_tour_availability:
            phase = PHASE_CONFIGS["TOUR_SCHEDULING"].name
            phase_instructions = PHASE_CONFIGS["TOUR_SCHEDULING"].instructions
        elif missing_fields:
            phase = PHASE_CONFIGS["QUALIFICATION"].name
            missing_fields_str = ", ".join(missing_fields)
            phase_instructions = PHASE_CONFIGS["QUALIFICATION"].instructions.format(
                missing_fields=missing_fields_str
            )
        elif missing_optional and len(missing_optional) > 0:
            phase = PHASE_CONFIGS["OPTIONAL_QUESTIONS"].name
            missing_optional_str = ", ".join(missing_optional)
            phase_instructions = PHASE_CONFIGS[
                "OPTIONAL_QUESTIONS"
            ].instructions.format(missing_optional=missing_optional_str)
        else:
            phase = PHASE_CONFIGS["COMPLETE"].name
            phase_instructions = PHASE_CONFIGS["COMPLETE"].instructions
        return phase, phase_instructions

    async def extract_lead_info(self, message: str, lead: Lead) -> Dict[str, Any]:
        """Extract lead information from message"""
        try:
            current_data = lead.to_dict()
            print(f"[DEBUG] Current lead data before extraction: {current_data}")

            context = {
                "move_in_date": current_data.get("move_in_date", "EMPTY"),
                "price": current_data.get("price", "EMPTY"),
                "beds": current_data.get("beds", "EMPTY"),
                "baths": current_data.get("baths", "EMPTY"),
                "location": current_data.get("location", "EMPTY"),
                "amenities": current_data.get("amenities", "EMPTY"),
                "tour_availability": current_data.get("tour_availability", "EMPTY"),
                "rental_urgency": current_data.get("rental_urgency", "EMPTY"),
                "boston_rental_experience": current_data.get(
                    "boston_rental_experience", "EMPTY"
                ),
                "message": message,
            }

            system_prompt = self.prompt_loader.render("extraction.tmpl", context)
            print(f"[DEBUG] Extraction prompt: {system_prompt}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Extract ALL information from: {message}",
                    },
                ],
                max_tokens=300,
                temperature=0.1,
            )

            result_text = response.choices[0].message.content
            if result_text is None:
                raise ValueError("OpenAI returned None content")
            result_text = result_text.strip()

            extracted_info = json.loads(result_text)
            print(
                f"[DEBUG] Extract attempt for message '{message}': {result_text} | Successfully extracted: {extracted_info}"
            )
            return extracted_info

        except Exception as e:
            print(f"[ERROR] Failed to extract lead info from '{message}': {e}")
            return {}

    async def generate_response(
        self,
        lead: Lead,
        message: str,
        missing_fields: List[str],
        needs_tour_availability: bool = False,
        missing_optional: Optional[List[str]] = None,
    ) -> str:
        """Generate AI response based on lead state"""
        try:
            lead_data = lead.to_dict()

            print(f"[DEBUG] Lead data at response generation: {lead_data}")
            print(f"[DEBUG] Missing fields: {missing_fields}")
            print(f"[DEBUG] Missing optional: {missing_optional}")

            # Get database status
            database_status = self._get_database_status(lead_data)
            print(f"[DEBUG] Database status: {database_status}")

            # Get chat history
            chat_history = self._get_chat_history(lead_data)

            # Get phase instructions
            phase, phase_instructions = self._get_phase_instructions(
                needs_tour_availability, missing_fields, missing_optional
            )

            # Build the prompt
            context = {
                "database_status": database_status,
                "chat_history": chat_history,
                "phase": phase,
                "phase_instructions": phase_instructions,
                "incoming_message": message,
            }

            system_prompt = self.prompt_loader.render(
                "qualification_system.tmpl", context
            )

            print(f"[DEBUG] Qualification prompt: {system_prompt}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                max_tokens=300,
                temperature=0.7,
            )

            result_text = response.choices[0].message.content
            if result_text is None:
                raise ValueError("OpenAI returned None content")

            return result_text.strip()

        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "I'm having trouble processing your message. Please try again."

    async def generate_delay_response(self, delay_info: Dict[str, Any]) -> str:
        """Generate response for delay requests"""
        try:
            delay_days = delay_info["delay_days"]
            if delay_days == 1:
                time_phrase = "tomorrow"
            elif delay_days <= 7:
                time_phrase = f"in {delay_days} days"
            elif delay_days <= 30:
                weeks = delay_days // 7
                time_phrase = f"in {weeks} week{'s' if weeks > 1 else ''}"
            else:
                months = delay_days // 30
                time_phrase = f"in {months} month{'s' if months > 1 else ''}"

            return f"No problem! I'll reach out {time_phrase}. Feel free to message me anytime if you have questions before then."
        except Exception as e:
            print(f"Error generating delay response: {e}")
            return "I'll follow up with you later. Feel free to message me anytime!"

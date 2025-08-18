import os
import openai
from typing import Dict, List, Optional, Tuple

from utils.prompt_loader import PromptLoader
from utils.constants import PHASE_CONFIGS, REQUIRED_FIELDS, OPTIONAL_FIELDS
from datetime import datetime
from typing import TypedDict
import json


class DelayResult(TypedDict):
    delay_days: int
    delay_type: str
    original_text: str


class OpenAIClient:
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
        # Include chat history for better conversational context
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

    def generate_response(
        self,
        lead_data: Dict,
        incoming_message: str,
        missing_fields: List[str],
        needs_tour_availability: bool = False,
        missing_optional: Optional[List[str]] = None,
    ) -> str:
        """Generate a conversational response based on lead data and missing fields"""

        if missing_optional is None:
            missing_optional = []

        database_status_str = self._get_database_status(lead_data)
        chat_history_str = self._get_chat_history(lead_data)

        phase, phase_instructions = self._get_phase_instructions(
            needs_tour_availability, missing_fields, missing_optional
        )

        system_prompt = self.prompt_loader.render(
            "qualification_system.tmpl",
            {
                "phase": phase,
                "chat_history": chat_history_str,
                "database_status": database_status_str,
                "phase_instructions": phase_instructions,
                "incoming_message": incoming_message,
            },
        )

        user_prompt = self.prompt_loader.render("user_prompt.tmpl", {})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=200,
                temperature=0.5,
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

        try:
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
            print(f"[DEBUG] Extract attempt for message '{message}': {result_text}")

            extracted_info = json.loads(result_text)
            print(f"[DEBUG] Successfully extracted: {extracted_info}")
            return extracted_info

        except Exception as e:
            print(f"[ERROR] Failed to extract lead info from '{message}': {e}")
            return {}

    def detect_delay(
        self, message: str, reference_time: Optional[datetime] = None
    ) -> DelayResult:
        if reference_time is None:
            reference_time = datetime.now()

        delay_prompt = self.prompt_loader.render("delay.tmpl", {})

        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": delay_prompt,
                    },
                    {"role": "user", "content": message},
                ],
                response_format={"type": "json_object"},
                max_tokens=100,
                temperature=0.1,
            )

            # The SDK may still give content as string, so parse safely
            content = resp.choices[0].message.content
            if not content:
                raise ValueError("OpenAI returned empty content")
            
            data = json.loads(content)
            
            # Extract the delay information
            has_delay = data.get("has_delay", False)
            delay_days = data.get("delay_days", 0)
            delay_type = data.get("delay_type", "default")
            
            # Ensure delay_days is non-negative
            if delay_days < 0:
                delay_days = 0
                delay_type = "default"

            return {
                "delay_days": delay_days,
                "delay_type": delay_type,
                "original_text": message,
            }

        except Exception as e:
            print(f"[WARN] Failed to detect delay for '{message}': {e}")
            return {
                "delay_days": 7,
                "delay_type": "default",
                "original_text": message,
            }

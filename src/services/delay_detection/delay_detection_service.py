import os
import openai
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from src.services.interfaces import IDelayDetectionService
from src.utils.prompt_loader import PromptLoader


class DelayDetectionService(IDelayDetectionService):
    """Delay detection service implementation - migrated from legacy client"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY environment variable")

        self.client = openai.OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.prompt_loader = PromptLoader()
    
    async def detect_delay_request(self, message: str) -> Optional[Dict[str, Any]]:
        """Detect if message contains delay request"""
        try:
            delay_prompt = self.prompt_loader.render("delay.tmpl", {})

            response = self.client.chat.completions.create(
                model=self.model,
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
            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenAI returned empty content")

            data = json.loads(content)

            # Extract the delay information
            delay_days = data.get("delay_days", 0)
            delay_type = data.get("delay_type", "default")

            # Ensure delay_days is non-negative
            if delay_days < 0:
                delay_days = 0
                delay_type = "default"

            result = {
                "delay_days": delay_days,
                "delay_type": delay_type,
                "original_text": message,
            }
            
            if delay_days > 0:
                return result
            return None
            
        except Exception as e:
            print(f"Error detecting delay request: {e}")
            return None
    
    async def calculate_delay_until(self, delay_info: Dict[str, Any]) -> str:
        """Calculate delay until time"""
        try:
            delay_days = delay_info.get("delay_days", 7)
            delay_until = datetime.now() + timedelta(days=delay_days)
            return delay_until.isoformat()
        except Exception as e:
            print(f"Error calculating delay: {e}")
            # Fallback to 7 days
            return (datetime.now() + timedelta(days=7)).isoformat()

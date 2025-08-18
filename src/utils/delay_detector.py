from datetime import datetime
from typing import TypedDict, Optional
from utils.openai_client import OpenAIClient


class DelayResult(TypedDict):
    delay_days: int
    delay_type: str
    original_text: str


class DelayDetector:
    """Detects explicit delay handling using LLM-backed datetime parsing"""

    def __init__(self):
        # Use existing OpenAIClient or create one
        self.client = OpenAIClient()

    def detect_delay(
        self, message: str, reference_time: Optional[datetime] = None
    ) -> DelayResult:
        # Delegate to OpenAIClient
        return self.client.detect_delay(message, reference_time)

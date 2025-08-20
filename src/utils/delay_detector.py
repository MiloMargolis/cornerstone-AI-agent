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

    def detect_delay_request(self, message: str) -> Optional[DelayResult]:
        """
        Detect if the message is explicitly requesting a delay in follow-up.
        This is more specific than detect_delay() and avoids false positives
        from tour availability responses.
        """
        # First, check if this looks like tour availability (which should NOT be treated as delay)
        tour_availability_indicators = [
            "weekend", "weekends", "saturday", "sunday", "available", "free", "anytime",
            "morning", "afternoon", "evening", "tour", "visit", "see", "look at"
        ]
        
        message_lower = message.lower()
        if any(indicator in message_lower for indicator in tour_availability_indicators):
            return None  # This is likely tour availability, not a delay request
        
        # Now check for actual delay requests
        delay_indicators = [
            "not ready", "busy", "later", "call me in", "contact me in", "reach out in",
            "wait", "delay", "not now", "some other time", "maybe later"
        ]
        
        if any(indicator in message_lower for indicator in delay_indicators):
            return self.detect_delay(message)
        
        return None

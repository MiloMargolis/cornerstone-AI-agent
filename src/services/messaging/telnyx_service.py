import os
import telnyx
from typing import Dict, Any
from services.interfaces import IMessagingService


class TelnyxService(IMessagingService):
    """Telnyx messaging service implementation - migrated from legacy client"""
    
    def __init__(self):
        api_key = os.getenv("TELNYX_API_KEY")
        if not api_key:
            raise ValueError("Missing TELNYX_API_KEY environment variable")

        telnyx.api_key = api_key
        self.from_number = os.getenv("TELNYX_PHONE_NUMBER")
        if not self.from_number:
            raise ValueError("Missing TELNYX_PHONE_NUMBER environment variable")
        
        print(f"[DEBUG] TelnyxService initialized with from_number: {self.from_number}")
    
    async def send_sms(self, to: str, message: str) -> bool:
        """Send SMS message via Telnyx"""
        try:
            response = telnyx.Message.create(
                from_=self.from_number, to=to, text=message
            )

            print(f"SMS sent successfully to {to}: {response.id}")
            return True

        except Exception as e:
            print(f"Error sending SMS to {to}: {e}")
            return False
    
    async def send_agent_notification(self, agent_phone: str, message: str) -> bool:
        """Send notification to agent"""
        try:
            return await self.send_sms(agent_phone, message)
        except Exception as e:
            print(f"Error sending agent notification to {agent_phone}: {e}")
            return False


class MockTelnyxService(IMessagingService):
    """Mock Telnyx service for testing"""
    
    def __init__(self):
        self.from_number = os.getenv("TELNYX_PHONE_NUMBER", "+1234567890")

    async def send_sms(self, to: str, message: str) -> bool:
        print(f"[MOCK] SMS to {to} from {self.from_number}: {message}")
        return True

    async def send_agent_notification(self, agent_phone: str, message: str) -> bool:
        print(f"[MOCK] Agent notification to {agent_phone}: {message}")
        return True

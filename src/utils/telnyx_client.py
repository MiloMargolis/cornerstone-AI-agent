import os
import telnyx
from typing import Optional

class TelnyxClient:
    def __init__(self):
        api_key = os.getenv("TELNYX_API_KEY")
        if not api_key:
            raise ValueError("Missing TELNYX_API_KEY environment variable")
        
        telnyx.api_key = api_key
        self.from_number = os.getenv("TELNYX_PHONE_NUMBER")
        if not self.from_number:
            raise ValueError("Missing TELNYX_PHONE_NUMBER environment variable")
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS message to a phone number"""
        try:
            response = telnyx.Message.create(
                from_=self.from_number,
                to=to_number,
                text=message
            )
            
            print(f"SMS sent successfully to {to_number}: {response.id}")
            return True
            
        except Exception as e:
            print(f"Error sending SMS to {to_number}: {e}")
            return False
    
    def send_group_sms(self, group_numbers: list, message: str) -> bool:
        """Send SMS message to multiple recipients (group chat)"""
        try:
            # For group messages, we need to send to all participants
            # Telnyx doesn't have native group messaging, so we send individual messages
            success_count = 0
            
            for number in group_numbers:
                if self.send_sms(number, message):
                    success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            print(f"Error sending group SMS: {e}")
            return False 
from typing import Dict, Any
from models.webhook import WebhookEvent
from core.lead_processor import LeadProcessor


class EventProcessor:
    """Event processor for handling webhook events"""
    
    def __init__(self, lead_processor: LeadProcessor):
        self.lead_processor = lead_processor
    
    async def process_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process webhook event"""
        try:
            # Extract message details
            from_number = event.payload.from_number
            message_text = event.payload.text
            
            # Process the lead message
            response = await self.lead_processor.process_lead_message(from_number, message_text)
            
            return {
                "success": True,
                "response": response,
                "event_id": event.event_id,
                "processed_at": event.timestamp
            }
            
        except Exception as e:
            # Log the error and return error response
            print(f"Error processing event: {e}")
            return {
                "success": False,
                "error": str(e),
                "event_id": event.event_id
            }
    
    async def validate_event(self, event: WebhookEvent) -> bool:
        """Validate webhook event"""
        try:
            # Check if event has required fields
            if not event.payload.from_number:
                print("Missing from phone number")
                return False
            
            if not event.payload.text:
                print("Missing message text")
                return False
            
            if not event.payload.to_numbers:
                print("Missing to phone numbers")
                return False
            
            # Validate phone number format (basic validation)
            if not self._is_valid_phone_number(event.payload.from_number):
                print(f"Invalid from phone number: {event.payload.from_number}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating event: {e}")
            return False
    
    def _is_valid_phone_number(self, phone: str) -> bool:
        """Basic phone number validation"""
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Check if it's a valid US phone number (10 or 11 digits)
        if len(digits) == 10:
            return True  # No country code
        elif len(digits) == 11 and digits.startswith('1'):
            return True  # With country code
        else:
            return False

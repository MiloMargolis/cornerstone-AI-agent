from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum


class EventType(Enum):
    """Supported webhook event types"""
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    MESSAGE_DELIVERED = "message.delivered"
    MESSAGE_FAILED = "message.failed"


@dataclass
class MessagePayload:
    """Message payload structure"""
    from_number: str
    to_numbers: List[str]
    text: str
    message_id: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class WebhookEvent:
    """Webhook event data model with validation"""
    
    event_type: EventType
    payload: MessagePayload
    event_id: Optional[str] = None
    timestamp: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_telnyx_webhook(cls, webhook_data: Dict[str, Any]) -> "WebhookEvent":
        """Create WebhookEvent from Telnyx webhook data"""
        event_type_str = webhook_data.get("event_type")
        if not event_type_str:
            raise ValueError("Missing event_type in webhook data")
        
        try:
            event_type = EventType(event_type_str)
        except ValueError:
            raise ValueError(f"Unsupported event type: {event_type_str}")
        
        payload_data = webhook_data.get("payload", {})
        
        # Extract from number
        from_data = payload_data.get("from", {})
        from_number = from_data.get("phone_number")
        if not from_number:
            raise ValueError("Missing from phone number in webhook payload")
        
        # Extract to numbers (list)
        to_list = payload_data.get("to", [])
        to_numbers = [item.get("phone_number") for item in to_list if item.get("phone_number")]
        if not to_numbers:
            raise ValueError("Missing to phone numbers in webhook payload")
        
        # Extract message text
        text = payload_data.get("text")
        if not text:
            raise ValueError("Missing message text in webhook payload")
        
        payload = MessagePayload(
            from_number=from_number,
            to_numbers=to_numbers,
            text=text,
            message_id=payload_data.get("id"),
            timestamp=payload_data.get("timestamp")
        )
        
        return cls(
            event_type=event_type,
            payload=payload,
            event_id=webhook_data.get("id"),
            timestamp=webhook_data.get("timestamp"),
            raw_data=webhook_data
        )
    
    def is_message_received(self) -> bool:
        """Check if this is a message received event"""
        return self.event_type == EventType.MESSAGE_RECEIVED
    
    def is_from_agent(self, agent_phone: str) -> bool:
        """Check if message is from the agent"""
        return self.payload.from_number == agent_phone
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_type": self.event_type.value,
            "payload": {
                "from_number": self.payload.from_number,
                "to_numbers": self.payload.to_numbers,
                "text": self.payload.text,
                "message_id": self.payload.message_id,
                "timestamp": self.payload.timestamp,
            },
            "event_id": self.event_id,
            "timestamp": self.timestamp,
        }

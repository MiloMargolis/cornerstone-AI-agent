import pytest
from src.models.webhook import WebhookEvent, MessagePayload, EventType


class TestWebhookEvent:
    """Test cases for WebhookEvent data model"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.valid_webhook_data = {
            "event_type": "message.received",
            "id": "test-event-123",
            "timestamp": "2024-01-01T10:00:00Z",
            "payload": {
                "from": {"phone_number": "+1234567890"},
                "to": [{"phone_number": "+1987654321"}],
                "text": "Hello there",
                "id": "msg-123",
                "timestamp": "2024-01-01T10:00:00Z"
            }
        }
    
    def test_from_telnyx_webhook_valid_data(self):
        """Test creating WebhookEvent from valid Telnyx webhook data"""
        event = WebhookEvent.from_telnyx_webhook(self.valid_webhook_data)
        
        assert event.event_type == EventType.MESSAGE_RECEIVED
        assert event.event_id == "test-event-123"
        assert event.timestamp == "2024-01-01T10:00:00Z"
        assert event.payload.from_number == "+1234567890"
        assert event.payload.to_numbers == ["+1987654321"]
        assert event.payload.text == "Hello there"
        assert event.payload.message_id == "msg-123"
        assert event.payload.timestamp == "2024-01-01T10:00:00Z"
        assert event.raw_data == self.valid_webhook_data
    
    def test_from_telnyx_webhook_missing_event_type(self):
        """Test creating WebhookEvent with missing event_type"""
        invalid_data = self.valid_webhook_data.copy()
        del invalid_data["event_type"]
        
        with pytest.raises(ValueError, match="Missing event_type in webhook data"):
            WebhookEvent.from_telnyx_webhook(invalid_data)
    
    def test_from_telnyx_webhook_unsupported_event_type(self):
        """Test creating WebhookEvent with unsupported event type"""
        invalid_data = self.valid_webhook_data.copy()
        invalid_data["event_type"] = "unsupported.event"
        
        with pytest.raises(ValueError, match="Unsupported event type"):
            WebhookEvent.from_telnyx_webhook(invalid_data)
    
    def test_from_telnyx_webhook_missing_from_number(self):
        """Test creating WebhookEvent with missing from phone number"""
        invalid_data = self.valid_webhook_data.copy()
        invalid_data["payload"]["from"] = {}
        
        with pytest.raises(ValueError, match="Missing from phone number"):
            WebhookEvent.from_telnyx_webhook(invalid_data)
    
    def test_from_telnyx_webhook_missing_to_numbers(self):
        """Test creating WebhookEvent with missing to phone numbers"""
        invalid_data = self.valid_webhook_data.copy()
        invalid_data["payload"]["to"] = []
        
        with pytest.raises(ValueError, match="Missing to phone numbers"):
            WebhookEvent.from_telnyx_webhook(invalid_data)
    
    def test_from_telnyx_webhook_missing_text(self):
        """Test creating WebhookEvent with missing message text"""
        invalid_data = self.valid_webhook_data.copy()
        invalid_data["payload"]["text"] = ""
        
        with pytest.raises(ValueError, match="Missing message text"):
            WebhookEvent.from_telnyx_webhook(invalid_data)
    
    def test_from_telnyx_webhook_multiple_to_numbers(self):
        """Test creating WebhookEvent with multiple to phone numbers"""
        data = self.valid_webhook_data.copy()
        data["payload"]["to"] = [
            {"phone_number": "+1987654321"},
            {"phone_number": "+1987654322"}
        ]
        
        event = WebhookEvent.from_telnyx_webhook(data)
        
        assert event.payload.to_numbers == ["+1987654321", "+1987654322"]
    
    def test_from_telnyx_webhook_missing_optional_fields(self):
        """Test creating WebhookEvent with missing optional fields"""
        data = self.valid_webhook_data.copy()
        del data["payload"]["id"]
        del data["payload"]["timestamp"]
        
        event = WebhookEvent.from_telnyx_webhook(data)
        
        assert event.payload.message_id is None
        assert event.payload.timestamp is None
    
    def test_is_message_received_true(self):
        """Test is_message_received when event type is message.received"""
        event = WebhookEvent.from_telnyx_webhook(self.valid_webhook_data)
        
        assert event.is_message_received() is True
    
    def test_is_message_received_false(self):
        """Test is_message_received when event type is not message.received"""
        data = self.valid_webhook_data.copy()
        data["event_type"] = "message.sent"
        
        event = WebhookEvent.from_telnyx_webhook(data)
        
        assert event.is_message_received() is False
    
    def test_is_from_agent_true(self):
        """Test is_from_agent when message is from agent"""
        event = WebhookEvent.from_telnyx_webhook(self.valid_webhook_data)
        agent_phone = "+1234567890"
        
        assert event.is_from_agent(agent_phone) is True
    
    def test_is_from_agent_false(self):
        """Test is_from_agent when message is not from agent"""
        event = WebhookEvent.from_telnyx_webhook(self.valid_webhook_data)
        agent_phone = "+1987654321"
        
        assert event.is_from_agent(agent_phone) is False
    
    def test_to_dict(self):
        """Test converting WebhookEvent to dictionary"""
        event = WebhookEvent.from_telnyx_webhook(self.valid_webhook_data)
        
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "message.received"
        assert event_dict["event_id"] == "test-event-123"
        assert event_dict["timestamp"] == "2024-01-01T10:00:00Z"
        assert event_dict["payload"]["from_number"] == "+1234567890"
        assert event_dict["payload"]["to_numbers"] == ["+1987654321"]
        assert event_dict["payload"]["text"] == "Hello there"
        assert event_dict["payload"]["message_id"] == "msg-123"
        assert event_dict["payload"]["timestamp"] == "2024-01-01T10:00:00Z"
    
    def test_message_payload_creation(self):
        """Test creating MessagePayload directly"""
        payload = MessagePayload(
            from_number="+1234567890",
            to_numbers=["+1987654321"],
            text="Hello there",
            message_id="msg-123",
            timestamp="2024-01-01T10:00:00Z"
        )
        
        assert payload.from_number == "+1234567890"
        assert payload.to_numbers == ["+1987654321"]
        assert payload.text == "Hello there"
        assert payload.message_id == "msg-123"
        assert payload.timestamp == "2024-01-01T10:00:00Z"
    
    def test_message_payload_creation_minimal(self):
        """Test creating MessagePayload with minimal required fields"""
        payload = MessagePayload(
            from_number="+1234567890",
            to_numbers=["+1987654321"],
            text="Hello there"
        )
        
        assert payload.from_number == "+1234567890"
        assert payload.to_numbers == ["+1987654321"]
        assert payload.text == "Hello there"
        assert payload.message_id is None
        assert payload.timestamp is None
    
    def test_event_type_enum(self):
        """Test EventType enum values"""
        assert EventType.MESSAGE_RECEIVED == "message.received"
        assert EventType.MESSAGE_SENT == "message.sent"
        assert EventType.MESSAGE_DELIVERED == "message.delivered"
        assert EventType.MESSAGE_FAILED == "message.failed"
    
    def test_webhook_event_creation_direct(self):
        """Test creating WebhookEvent directly"""
        payload = MessagePayload(
            from_number="+1234567890",
            to_numbers=["+1987654321"],
            text="Hello there"
        )
        
        event = WebhookEvent(
            event_type=EventType.MESSAGE_RECEIVED,
            payload=payload,
            event_id="test-123",
            timestamp="2024-01-01T10:00:00Z"
        )
        
        assert event.event_type == EventType.MESSAGE_RECEIVED
        assert event.payload == payload
        assert event.event_id == "test-123"
        assert event.timestamp == "2024-01-01T10:00:00Z"
        assert event.raw_data is None
    
    def test_webhook_event_creation_minimal(self):
        """Test creating WebhookEvent with minimal fields"""
        payload = MessagePayload(
            from_number="+1234567890",
            to_numbers=["+1987654321"],
            text="Hello there"
        )
        
        event = WebhookEvent(
            event_type=EventType.MESSAGE_RECEIVED,
            payload=payload
        )
        
        assert event.event_type == EventType.MESSAGE_RECEIVED
        assert event.payload == payload
        assert event.event_id is None
        assert event.timestamp is None
        assert event.raw_data is None

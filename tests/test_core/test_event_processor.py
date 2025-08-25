import pytest
from unittest.mock import Mock, AsyncMock
from src.core.event_processor import EventProcessor
from src.models.webhook import WebhookEvent, MessagePayload, EventType


class TestEventProcessor:
    """Test cases for EventProcessor webhook handling"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_lead_processor = Mock()
        self.mock_lead_processor.process_lead_message = AsyncMock()
        
        self.processor = EventProcessor(lead_processor=self.mock_lead_processor)
    
    @pytest.mark.asyncio
    async def test_validate_event_valid(self):
        """Test validating a valid webhook event"""
        payload = MessagePayload(
            from_number="+1234567890",
            to_numbers=["+1987654321"],
            text="Hello there"
        )
        event = WebhookEvent(
            event_type=EventType.MESSAGE_RECEIVED,
            payload=payload,
            event_id="test-123"
        )
        
        result = await self.processor.validate_event(event)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_event_invalid(self):
        """Test validating an invalid webhook event"""
        payload = MessagePayload(
            from_number="",  # Missing phone number
            to_numbers=["+1987654321"],
            text="Hello there"
        )
        event = WebhookEvent(
            event_type=EventType.MESSAGE_RECEIVED,
            payload=payload
        )
        
        result = await self.processor.validate_event(event)
        assert result is False
    
    def test_validate_phone_number(self):
        """Test phone number validation"""
        assert self.processor._is_valid_phone_number("1234567890") is True
        assert self.processor._is_valid_phone_number("+11234567890") is True
        assert self.processor._is_valid_phone_number("123456789") is False  # Too short
        assert self.processor._is_valid_phone_number("123456789012") is False  # Too long
    
    @pytest.mark.asyncio
    async def test_process_event_success(self):
        """Test successfully processing an event"""
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
        
        self.mock_lead_processor.process_lead_message.return_value = "Thanks for your message!"
        
        result = await self.processor.process_event(event)
        
        assert result["success"] is True
        assert result["response"] == "Thanks for your message!"
        assert result["event_id"] == "test-123"
        
        self.mock_lead_processor.process_lead_message.assert_called_once_with(
            "+1234567890", "Hello there"
        )
    
    @pytest.mark.asyncio
    async def test_process_event_error(self):
        """Test processing event when an error occurs"""
        payload = MessagePayload(
            from_number="+1234567890",
            to_numbers=["+1987654321"],
            text="Hello there"
        )
        event = WebhookEvent(
            event_type=EventType.MESSAGE_RECEIVED,
            payload=payload,
            event_id="test-123"
        )
        
        self.mock_lead_processor.process_lead_message.side_effect = Exception("Processing error")
        
        result = await self.processor.process_event(event)
        
        assert result["success"] is False
        assert result["error"] == "Processing error"
        assert result["event_id"] == "test-123"

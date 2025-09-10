import pytest
from unittest.mock import Mock, AsyncMock
from src.core.lead_processor import LeadProcessor
from src.models.lead import Lead


class TestLeadProcessor:
    """Test cases for LeadProcessor core business logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_lead_repo = Mock()
        self.mock_messaging = Mock()
        self.mock_ai_service = Mock()
        self.mock_delay_service = Mock()
        
        # Make async methods return values
        self.mock_lead_repo.get_by_phone = AsyncMock()
        self.mock_lead_repo.create = AsyncMock()
        self.mock_lead_repo.update = AsyncMock()
        self.mock_lead_repo.add_message_to_history = AsyncMock()
        self.mock_lead_repo.pause_follow_up_until = AsyncMock()
        self.mock_lead_repo.set_tour_ready = AsyncMock()
        self.mock_lead_repo.get_missing_fields = AsyncMock()
        self.mock_lead_repo.get_missing_optional_fields = AsyncMock()
        self.mock_lead_repo.needs_tour_availability = AsyncMock()
        self.mock_lead_repo.schedule_follow_up = AsyncMock()
        
        self.mock_messaging.send_sms = AsyncMock()
        self.mock_messaging.send_agent_notification = AsyncMock()
        
        self.mock_ai_service.extract_lead_info = AsyncMock()
        self.mock_ai_service.generate_response = AsyncMock()
        self.mock_ai_service.generate_delay_response = AsyncMock()
        
        self.mock_delay_service.detect_delay_request = AsyncMock()
        self.mock_delay_service.calculate_delay_until = AsyncMock()
        
        self.processor = LeadProcessor(
            lead_repository=self.mock_lead_repo,
            messaging_service=self.mock_messaging,
            ai_service=self.mock_ai_service,
            delay_detection_service=self.mock_delay_service
        )
    
    @pytest.mark.asyncio
    async def test_process_new_lead_message(self):
        """Test processing message from a new lead"""
        # Setup
        phone = "+1234567890"
        message = "Hi, I'm looking for a 2 bedroom apartment"
        
        self.mock_lead_repo.get_by_phone.return_value = None
        self.mock_lead_repo.create.return_value = Lead(phone=phone)
        self.mock_ai_service.extract_lead_info.return_value = {"beds": "2"}
        self.mock_lead_repo.update.return_value = Lead(phone=phone, beds="2")
        self.mock_ai_service.generate_response.return_value = "Great! What's your budget?"
        self.mock_messaging.send_sms.return_value = True
        
        # Mock delay detection to return None (no delay requested)
        self.mock_delay_service.detect_delay_request.return_value = None
        
        # Mock missing fields analysis
        self.mock_lead_repo.get_missing_fields.return_value = ["price"]
        self.mock_lead_repo.get_missing_optional_fields.return_value = []
        self.mock_lead_repo.needs_tour_availability.return_value = False
        
        # Execute
        result = await self.processor.process_lead_message(phone, message)
        
        # Verify
        assert result == "Great! What's your budget?"
        self.mock_lead_repo.get_by_phone.assert_called_once_with(phone)
        self.mock_lead_repo.create.assert_called_once()
        self.mock_ai_service.extract_lead_info.assert_called_once()
        self.mock_messaging.send_sms.assert_called_once_with(phone, "Great! What's your budget?")
    
    @pytest.mark.asyncio
    async def test_process_existing_lead_message(self):
        """Test processing message from an existing lead"""
        # Setup
        phone = "+1234567890"
        message = "My budget is $2000"
        existing_lead = Lead(phone=phone, beds="2")
        
        self.mock_lead_repo.get_by_phone.return_value = existing_lead
        self.mock_ai_service.extract_lead_info.return_value = {"price": "2000"}
        self.mock_lead_repo.update.return_value = Lead(phone=phone, beds="2", price="2000")
        self.mock_ai_service.generate_response.return_value = "Perfect! When do you want to move in?"
        self.mock_messaging.send_sms.return_value = True
        
        # Mock delay detection to return None (no delay requested)
        self.mock_delay_service.detect_delay_request.return_value = None
        
        # Mock missing fields analysis
        self.mock_lead_repo.get_missing_fields.return_value = ["move_in_date"]
        self.mock_lead_repo.get_missing_optional_fields.return_value = []
        self.mock_lead_repo.needs_tour_availability.return_value = False
        
        # Execute
        result = await self.processor.process_lead_message(phone, message)
        
        # Verify
        assert result == "Perfect! When do you want to move in?"
        self.mock_lead_repo.get_by_phone.assert_called_once_with(phone)
        self.mock_lead_repo.create.assert_not_called()
        self.mock_ai_service.extract_lead_info.assert_called_once_with(message, existing_lead)
    
    @pytest.mark.asyncio
    async def test_process_delay_request(self):
        """Test processing a delay request message"""
        # Setup
        phone = "+1234567890"
        message = "Can you follow up in 3 days?"
        
        existing_lead = Lead(phone=phone)
        self.mock_lead_repo.get_by_phone.return_value = existing_lead
        self.mock_delay_service.detect_delay_request.return_value = {"delay_days": 3}
        self.mock_delay_service.calculate_delay_until.return_value = "2024-01-15T10:00:00"
        self.mock_ai_service.generate_delay_response.return_value = "No problem! I'll reach out in 3 days."
        self.mock_messaging.send_sms.return_value = True
        
        # Mock extract_lead_info to return None (no new info extracted)
        self.mock_ai_service.extract_lead_info.return_value = None
        
        # Execute
        result = await self.processor.process_lead_message(phone, message)
        
        # Verify
        assert result == "No problem! I'll reach out in 3 days."
        self.mock_delay_service.detect_delay_request.assert_called_once_with(message)
        self.mock_lead_repo.pause_follow_up_until.assert_called_once_with(phone, "2024-01-15T10:00:00")
    
    @pytest.mark.asyncio
    async def test_process_message_with_fallback_on_error(self):
        """Test processing message when an error occurs"""
        # Setup
        phone = "+1234567890"
        message = "Hi there"
        
        self.mock_lead_repo.get_by_phone.side_effect = Exception("Database error")
        self.mock_messaging.send_sms.return_value = True
        
        # Execute
        result = await self.processor.process_lead_message(phone, message)
        
        # Verify
        assert result == "Thanks for your message. Our agent will follow up with you soon."
        self.mock_messaging.send_sms.assert_called_once_with(phone, "Thanks for your message. Our agent will follow up with you soon.")

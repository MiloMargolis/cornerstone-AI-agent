import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
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
        
        # Execute
        result = await self.processor.process_lead_message(phone, message)
        
        # Verify
        assert result == "Great! What's your budget?"
        self.mock_lead_repo.get_by_phone.assert_called_once_with(phone)
        self.mock_lead_repo.create.assert_called_once()
        self.mock_ai_service.extract_lead_info.assert_called_once_with(message, pytest.approx(Lead(phone=phone)))
        self.mock_lead_repo.add_message_to_history.assert_called()
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
        
        # Execute
        result = await self.processor.process_lead_message(phone, message)
        
        # Verify
        assert result == "No problem! I'll reach out in 3 days."
        self.mock_delay_service.detect_delay_request.assert_called_once_with(message)
        self.mock_delay_service.calculate_delay_until.assert_called_once_with({"delay_days": 3})
        self.mock_lead_repo.pause_follow_up_until.assert_called_once_with(phone, "2024-01-15T10:00:00")
    
    @pytest.mark.asyncio
    async def test_process_tour_ready_lead(self):
        """Test processing message from a tour-ready lead (should stay silent)"""
        # Setup
        phone = "+1234567890"
        message = "I'm ready for a tour"
        
        existing_lead = Lead(phone=phone, tour_ready=True)
        self.mock_lead_repo.get_by_phone.return_value = existing_lead
        
        # Execute
        result = await self.processor.process_lead_message(phone, message)
        
        # Verify
        assert result == "SILENT_TOUR_READY"
        self.mock_messaging.send_sms.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_tour_availability_completion(self):
        """Test processing message that completes tour availability"""
        # Setup
        phone = "+1234567890"
        message = "I'm available Tuesday at 2pm"
        
        existing_lead = Lead(phone=phone, tour_ready=False)
        self.mock_lead_repo.get_by_phone.return_value = existing_lead
        self.mock_ai_service.extract_lead_info.return_value = {"tour_availability": "Tuesday 2pm"}
        self.mock_lead_repo.update.return_value = Lead(phone=phone, tour_availability="Tuesday 2pm")
        self.mock_messaging.send_sms.return_value = True
        
        # Mock environment variable
        with patch.dict('os.environ', {'AGENT_PHONE_NUMBER': '+1987654321'}):
            # Execute
            result = await self.processor.process_lead_message(phone, message)
        
        # Verify
        expected_response = ("Perfect! I have all the information I need. "
                           "I'll get my teammate to set up an exact time with you for the tour. "
                           "They'll be in touch soon.")
        assert result == expected_response
        self.mock_lead_repo.set_tour_ready.assert_called_once_with(phone)
        self.mock_messaging.send_agent_notification.assert_called_once()
    
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
    
    @pytest.mark.asyncio
    async def test_schedule_first_follow_up_for_new_incomplete_lead(self):
        """Test scheduling first follow-up for new incomplete lead"""
        # Setup
        phone = "+1234567890"
        message = "Hi, I'm interested"
        
        existing_lead = Lead(phone=phone, next_follow_up_time=None)
        self.mock_lead_repo.get_by_phone.return_value = existing_lead
        self.mock_ai_service.extract_lead_info.return_value = {}
        self.mock_lead_repo.update.return_value = existing_lead
        self.mock_lead_repo.get_missing_fields.return_value = ["price", "beds"]
        self.mock_lead_repo.needs_tour_availability.return_value = False
        self.mock_lead_repo.get_missing_optional_fields.return_value = []
        self.mock_ai_service.generate_response.return_value = "What's your budget?"
        self.mock_messaging.send_sms.return_value = True
        
        # Execute
        await self.processor.process_lead_message(phone, message)
        
        # Verify follow-up was scheduled
        self.mock_lead_repo.schedule_follow_up.assert_called_once()

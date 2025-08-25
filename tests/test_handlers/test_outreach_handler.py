import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from src.handlers.outreach_handler import (
    lambda_handler, validate_phone_number, extract_first_name, 
    send_initial_outreach_message
)
from src.models.lead import Lead


class TestOutreachHandler:
    """Test cases for outreach handler Lambda function"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.valid_event = {
            "phone_number": "+1234567890",
            "name": "John Doe"
        }
    
    @patch('src.handlers.outreach_handler.container')
    @patch('src.handlers.outreach_handler.ErrorHandler')
    def test_lambda_handler_success(self, mock_error_handler, mock_container):
        """Test successful outreach processing"""
        # Setup mocks
        mock_lead_repo = Mock()
        mock_lead_repo.get_by_phone = AsyncMock()
        mock_lead_repo.get_by_phone.return_value = None  # No existing lead
        mock_lead_repo.create = AsyncMock()
        mock_lead_repo.create.return_value = Lead(phone="+1234567890", name="John Doe")
        mock_lead_repo.add_message_to_history = AsyncMock()
        
        mock_messaging = Mock()
        mock_messaging.send_sms = AsyncMock()
        mock_messaging.send_sms.return_value = True
        
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        
        # Mock the container methods properly
        mock_container.build_services = Mock()
        mock_container.resolve.side_effect = [mock_lead_repo, mock_messaging, mock_error_handler_instance]
        
        # Execute
        result = lambda_handler(self.valid_event, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Initial outreach message sent successfully"
        
        mock_lead_repo.get_by_phone.assert_called_once_with("+11234567890")
        mock_lead_repo.create.assert_called_once()
        mock_messaging.send_sms.assert_called_once()
    
    @patch('src.handlers.outreach_handler.container')
    @patch('src.handlers.outreach_handler.ErrorHandler')
    def test_lambda_handler_invalid_phone_number(self, mock_error_handler, mock_container):
        """Test outreach processing with invalid phone number"""
        # Setup mocks
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        mock_error_handler_instance.handle_validation_error.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid phone number"})
        }
        
        mock_container.resolve.return_value = mock_error_handler_instance
        
        # Execute with invalid phone number
        invalid_event = {"phone_number": "invalid", "name": "John Doe"}
        result = lambda_handler(invalid_event, None)
        
        # Verify
        assert result["statusCode"] == 400
        mock_error_handler_instance.handle_validation_error.assert_called_once_with("Invalid phone number format")
    
    def test_validate_phone_number(self):
        """Test phone number validation"""
        # Valid formats
        assert validate_phone_number("1234567890") == "+11234567890"
        assert validate_phone_number("+11234567890") == "+11234567890"
        
        # Invalid formats
        assert validate_phone_number("123456789") is None  # Too short
        assert validate_phone_number("123456789012") is None  # Too long
        assert validate_phone_number("invalid") is None  # Non-numeric
    
    def test_extract_first_name(self):
        """Test first name extraction from full names"""
        assert extract_first_name("John Doe") == "John"
        assert extract_first_name("Mary Jane Smith") == "Mary"
        assert extract_first_name("Jean-Pierre") == "Jean-pierre"  # Case is normalized
        assert extract_first_name("") == ""
        assert extract_first_name(None) == ""
    
    @pytest.mark.asyncio
    async def test_send_initial_outreach_message_success(self):
        """Test successful initial outreach message sending"""
        # Setup
        lead = Lead(phone="+1234567890", name="John Doe")
        phone_number = "+1234567890"
        
        mock_lead_repo = Mock()
        mock_lead_repo.add_message_to_history = AsyncMock()
        
        mock_messaging = Mock()
        mock_messaging.send_sms = AsyncMock()
        mock_messaging.send_sms.return_value = True
        
        # Execute
        result = await send_initial_outreach_message(lead, phone_number, mock_lead_repo, mock_messaging)
        
        # Verify
        assert result is True
        mock_messaging.send_sms.assert_called_once()
        mock_lead_repo.add_message_to_history.assert_called_once()

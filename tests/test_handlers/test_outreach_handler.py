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
        
        mock_messaging = Mock()
        mock_messaging.send_sms = AsyncMock()
        mock_messaging.send_sms.return_value = True
        
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        
        mock_container.resolve.side_effect = [mock_lead_repo, mock_messaging, mock_error_handler_instance]
        
        # Execute
        result = lambda_handler(self.valid_event, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Initial outreach message sent successfully"
        
        mock_lead_repo.get_by_phone.assert_called_once_with("+1234567890")
        mock_lead_repo.create.assert_called_once()
        mock_messaging.send_sms.assert_called_once()
    
    @patch('src.handlers.outreach_handler.container')
    @patch('src.handlers.outreach_handler.ErrorHandler')
    def test_lambda_handler_missing_phone_number(self, mock_error_handler, mock_container):
        """Test outreach processing with missing phone number"""
        # Setup mocks
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        mock_error_handler_instance.handle_validation_error.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing phone number"})
        }
        
        mock_container.resolve.return_value = mock_error_handler_instance
        
        # Execute with missing phone number
        invalid_event = {"name": "John Doe"}
        result = lambda_handler(invalid_event, None)
        
        # Verify
        assert result["statusCode"] == 400
        mock_error_handler_instance.handle_validation_error.assert_called_once_with("Missing required field: phone_number")
    
    @patch('src.handlers.outreach_handler.container')
    @patch('src.handlers.outreach_handler.ErrorHandler')
    def test_lambda_handler_missing_name(self, mock_error_handler, mock_container):
        """Test outreach processing with missing name"""
        # Setup mocks
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        mock_error_handler_instance.handle_validation_error.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing name"})
        }
        
        mock_container.resolve.return_value = mock_error_handler_instance
        
        # Execute with missing name
        invalid_event = {"phone_number": "+1234567890"}
        result = lambda_handler(invalid_event, None)
        
        # Verify
        assert result["statusCode"] == 400
        mock_error_handler_instance.handle_validation_error.assert_called_once_with("Missing required field: name")
    
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
    
    @patch('src.handlers.outreach_handler.container')
    @patch('src.handlers.outreach_handler.ErrorHandler')
    def test_lambda_handler_existing_phone_number(self, mock_error_handler, mock_container):
        """Test outreach processing with existing phone number"""
        # Setup mocks
        mock_lead_repo = Mock()
        mock_lead_repo.get_by_phone = AsyncMock()
        mock_lead_repo.get_by_phone.return_value = Lead(phone="+1234567890", name="Existing Lead")
        
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        mock_error_handler_instance.handle_validation_error.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Phone number exists"})
        }
        
        mock_container.resolve.side_effect = [mock_lead_repo, mock_error_handler_instance]
        
        # Execute
        result = lambda_handler(self.valid_event, None)
        
        # Verify
        assert result["statusCode"] == 400
        mock_error_handler_instance.handle_validation_error.assert_called_once_with("Phone number already exists in the database")
    
    @patch('src.handlers.outreach_handler.container')
    @patch('src.handlers.outreach_handler.ErrorHandler')
    def test_lambda_handler_lead_creation_failure(self, mock_error_handler, mock_container):
        """Test outreach processing when lead creation fails"""
        # Setup mocks
        mock_lead_repo = Mock()
        mock_lead_repo.get_by_phone = AsyncMock()
        mock_lead_repo.get_by_phone.return_value = None
        mock_lead_repo.create = AsyncMock()
        mock_lead_repo.create.return_value = None  # Creation failed
        
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        mock_error_handler_instance.handle_internal_error.return_value = {
            "statusCode": 500,
            "body": json.dumps({"error": "Creation failed"})
        }
        
        mock_container.resolve.side_effect = [mock_lead_repo, mock_error_handler_instance]
        
        # Execute
        result = lambda_handler(self.valid_event, None)
        
        # Verify
        assert result["statusCode"] == 500
        mock_error_handler_instance.handle_internal_error.assert_called_once_with("Failed to create lead record")
    
    def test_validate_phone_number_valid_formats(self):
        """Test phone number validation with various valid formats"""
        # 10 digits without country code
        assert validate_phone_number("1234567890") == "+11234567890"
        assert validate_phone_number("(123) 456-7890") == "+11234567890"
        assert validate_phone_number("123-456-7890") == "+11234567890"
        assert validate_phone_number("123.456.7890") == "+11234567890"
        
        # 11 digits with country code
        assert validate_phone_number("+11234567890") == "+11234567890"
        assert validate_phone_number("11234567890") == "+11234567890"
    
    def test_validate_phone_number_invalid_formats(self):
        """Test phone number validation with invalid formats"""
        assert validate_phone_number("123456789") is None  # Too short
        assert validate_phone_number("12345678901") is None  # Too long
        assert validate_phone_number("+21234567890") is None  # Wrong country code
        assert validate_phone_number("") is None  # Empty
        assert validate_phone_number("invalid") is None  # Non-numeric
    
    def test_extract_first_name(self):
        """Test first name extraction from full names"""
        assert extract_first_name("John Doe") == "John"
        assert extract_first_name("Mary Jane Smith") == "Mary"
        assert extract_first_name("Jean-Pierre") == "Jean-Pierre"
        assert extract_first_name("O'Connor") == "O'Connor"
        assert extract_first_name("  John  Doe  ") == "John"  # Whitespace
        assert extract_first_name("") == ""
        assert extract_first_name(None) == ""
        assert extract_first_name("John123") == "John"  # Removes numbers
        assert extract_first_name("John@Doe") == "John"  # Removes special chars
    
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
        
        # Check the message content
        call_args = mock_messaging.send_sms.call_args
        assert call_args[0][0] == phone_number
        assert "Hi John," in call_args[0][1]
        assert "Cornerstone Real Estate" in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_send_initial_outreach_message_no_name(self):
        """Test initial outreach message with no name"""
        # Setup
        lead = Lead(phone="+1234567890", name=None)
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
        call_args = mock_messaging.send_sms.call_args
        assert "Hi, " in call_args[0][1]  # Generic greeting
    
    @pytest.mark.asyncio
    async def test_send_initial_outreach_message_sms_failure(self):
        """Test initial outreach message when SMS fails"""
        # Setup
        lead = Lead(phone="+1234567890", name="John Doe")
        phone_number = "+1234567890"
        
        mock_lead_repo = Mock()
        mock_messaging = Mock()
        mock_messaging.send_sms = AsyncMock()
        mock_messaging.send_sms.return_value = False
        
        # Execute
        result = await send_initial_outreach_message(lead, phone_number, mock_lead_repo, mock_messaging)
        
        # Verify
        assert result is False
        mock_messaging.send_sms.assert_called_once()
        mock_lead_repo.add_message_to_history.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_initial_outreach_message_exception(self):
        """Test initial outreach message when an exception occurs"""
        # Setup
        lead = Lead(phone="+1234567890", name="John Doe")
        phone_number = "+1234567890"
        
        mock_lead_repo = Mock()
        mock_messaging = Mock()
        mock_messaging.send_sms = AsyncMock()
        mock_messaging.send_sms.side_effect = Exception("SMS error")
        
        # Execute
        result = await send_initial_outreach_message(lead, phone_number, mock_lead_repo, mock_messaging)
        
        # Verify
        assert result is False

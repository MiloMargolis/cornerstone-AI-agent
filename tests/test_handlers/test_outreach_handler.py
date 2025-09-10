import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from src.handlers.outreach_handler import lambda_handler, get_services


class TestOutreachHandler:
    """Test cases for outreach handler Lambda function"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.valid_event = {
            "phone_number": "+1234567890",
            "name": "John Doe"
        }
    
    @patch('src.handlers.outreach_handler.LeadRepository')
    @patch('src.handlers.outreach_handler.TelnyxService')
    def test_lambda_handler_success(self, mock_telnyx, mock_lead_repo):
        """Test successful outreach processing"""
        # Setup mocks
        mock_lead_repo_instance = Mock()
        mock_lead_repo_instance.get_by_phone = AsyncMock(return_value=None)  # No existing lead
        mock_lead_repo_instance.create = AsyncMock(return_value=Mock(phone="+1234567890", name="John Doe"))
        mock_lead_repo_instance.add_message_to_history = AsyncMock(return_value=True)
        mock_lead_repo.return_value = mock_lead_repo_instance
        
        mock_telnyx_instance = Mock()
        mock_telnyx_instance.send_sms = AsyncMock(return_value=True)
        mock_telnyx.return_value = mock_telnyx_instance
        
        # Execute
        result = lambda_handler(self.valid_event, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Initial outreach message sent successfully"
    
    @patch('src.handlers.outreach_handler.LeadRepository')
    @patch('src.handlers.outreach_handler.TelnyxService')
    def test_lambda_handler_existing_lead(self, mock_telnyx, mock_lead_repo):
        """Test outreach processing when lead already exists"""
        # Setup mocks
        mock_lead_repo_instance = Mock()
        mock_lead_repo_instance.get_by_phone = AsyncMock(return_value=Mock())  # Existing lead
        mock_lead_repo.return_value = mock_lead_repo_instance
        
        mock_telnyx_instance = Mock()
        mock_telnyx.return_value = mock_telnyx_instance
        
        # Execute
        result = lambda_handler(self.valid_event, None)
        
        # Verify
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "already exists" in body["error"]
    
    def test_lambda_handler_missing_phone(self):
        """Test outreach processing with missing phone number"""
        invalid_event = {"name": "John Doe"}
        
        result = lambda_handler(invalid_event, None)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "phone_number" in body["error"]
    
    def test_lambda_handler_missing_name(self):
        """Test outreach processing with missing name"""
        invalid_event = {"phone_number": "+1234567890"}
        
        result = lambda_handler(invalid_event, None)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "name" in body["error"]
    
    def test_lambda_handler_invalid_phone(self):
        """Test outreach processing with invalid phone number"""
        invalid_event = {
            "phone_number": "invalid",
            "name": "John Doe"
        }
        
        result = lambda_handler(invalid_event, None)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid phone number" in body["error"]
    
    @patch('src.handlers.outreach_handler.LeadRepository')
    @patch('src.handlers.outreach_handler.TelnyxService')
    def test_lambda_handler_sms_failure(self, mock_telnyx, mock_lead_repo):
        """Test outreach processing when SMS fails"""
        # Setup mocks
        mock_lead_repo_instance = Mock()
        mock_lead_repo_instance.get_by_phone = AsyncMock(return_value=None)
        mock_lead_repo_instance.create = AsyncMock(return_value=Mock(phone="+1234567890", name="John Doe"))
        mock_lead_repo.return_value = mock_lead_repo_instance
        
        mock_telnyx_instance = Mock()
        mock_telnyx_instance.send_sms = AsyncMock(return_value=False)
        mock_telnyx.return_value = mock_telnyx_instance
        
        # Execute
        result = lambda_handler(self.valid_event, None)
        
        # Verify
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "Failed to send" in body["error"]

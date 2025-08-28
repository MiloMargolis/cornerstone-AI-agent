import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from src.handlers.follow_up_handler import lambda_handler, get_services


class TestFollowUpHandler:
    """Test cases for follow-up handler Lambda function"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_lead = Mock()
        self.mock_lead.phone = "+1234567890"
        self.mock_lead.follow_up_count = 1
        self.mock_lead.follow_up_stage = "second"
    
    @patch('src.handlers.follow_up_handler.LeadRepository')
    @patch('src.handlers.follow_up_handler.TelnyxService')
    def test_lambda_handler_success(self, mock_telnyx, mock_lead_repo):
        """Test successful follow-up processing"""
        # Setup mocks
        mock_lead_repo_instance = Mock()
        mock_lead_repo_instance.get_leads_needing_follow_up = AsyncMock(return_value=[self.mock_lead])
        mock_lead_repo_instance.add_message_to_history = AsyncMock(return_value=True)
        mock_lead_repo_instance.update = AsyncMock(return_value=True)
        mock_lead_repo_instance.schedule_follow_up = AsyncMock(return_value=True)
        mock_lead_repo.return_value = mock_lead_repo_instance
        
        mock_telnyx_instance = Mock()
        mock_telnyx_instance.send_sms = AsyncMock(return_value=True)
        mock_telnyx.return_value = mock_telnyx_instance
        
        # Execute
        result = lambda_handler({}, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Follow-up processing completed"
        assert body["successful_follow_ups"] == 1
        assert body["failed_follow_ups"] == 0
        assert body["total_leads_processed"] == 1
    
    @patch('src.handlers.follow_up_handler.LeadRepository')
    @patch('src.handlers.follow_up_handler.TelnyxService')
    def test_lambda_handler_no_leads(self, mock_telnyx, mock_lead_repo):
        """Test follow-up processing when no leads need follow-up"""
        # Setup mocks
        mock_lead_repo_instance = Mock()
        mock_lead_repo_instance.get_leads_needing_follow_up = AsyncMock(return_value=[])
        mock_lead_repo.return_value = mock_lead_repo_instance
        
        mock_telnyx_instance = Mock()
        mock_telnyx.return_value = mock_telnyx_instance
        
        # Execute
        result = lambda_handler({}, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["total_leads_processed"] == 0
        assert body["successful_follow_ups"] == 0
        assert body["failed_follow_ups"] == 0
    
    @patch('src.handlers.follow_up_handler.LeadRepository')
    @patch('src.handlers.follow_up_handler.TelnyxService')
    def test_lambda_handler_error(self, mock_telnyx, mock_lead_repo):
        """Test follow-up processing when an error occurs"""
        # Setup mocks to raise an exception
        mock_lead_repo_instance = Mock()
        mock_lead_repo_instance.get_leads_needing_follow_up = AsyncMock(side_effect=Exception("Database error"))
        mock_lead_repo.return_value = mock_lead_repo_instance
        
        mock_telnyx_instance = Mock()
        mock_telnyx.return_value = mock_telnyx_instance
        
        # Execute
        result = lambda_handler({}, None)
        
        # Verify
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "error" in body

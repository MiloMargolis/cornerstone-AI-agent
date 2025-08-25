import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from src.handlers.follow_up_handler import lambda_handler, process_follow_up
from src.models.lead import Lead


class TestFollowUpHandler:
    """Test cases for follow-up handler Lambda function"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.test_lead = Lead(
            phone="+1234567890",
            name="John Doe",
            follow_up_count=1,
            follow_up_stage="second"
        )
    
    @patch('src.handlers.follow_up_handler.container')
    def test_lambda_handler_success(self, mock_container):
        """Test successful follow-up processing"""
        # Setup mocks
        mock_lead_repo = Mock()
        mock_lead_repo.get_leads_needing_follow_up = AsyncMock()
        mock_lead_repo.get_leads_needing_follow_up.return_value = [self.test_lead]
        mock_lead_repo.add_message_to_history = AsyncMock()
        mock_lead_repo.update = AsyncMock()
        mock_lead_repo.schedule_follow_up = AsyncMock()
        
        mock_messaging = Mock()
        mock_messaging.send_sms = AsyncMock()
        mock_messaging.send_sms.return_value = True
        
        # Mock container methods properly
        mock_container.build_services = Mock()
        mock_container.resolve.side_effect = [mock_lead_repo, mock_messaging]
        
        # Execute
        result = lambda_handler({}, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Follow-up processing completed"
        assert body["successful_follow_ups"] == 1
        assert body["failed_follow_ups"] == 0
        assert body["total_leads_processed"] == 1
        
        mock_lead_repo.get_leads_needing_follow_up.assert_called_once()
        mock_messaging.send_sms.assert_called_once()
    
    @patch('src.handlers.follow_up_handler.container')
    def test_lambda_handler_exception(self, mock_container):
        """Test follow-up processing when an exception occurs"""
        # Setup mocks
        mock_container.resolve.side_effect = Exception("Service error")
        
        # Execute
        result = lambda_handler({}, None)
        
        # Verify
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "error" in body
    
    @pytest.mark.asyncio
    async def test_process_follow_up_success(self):
        """Test successful follow-up processing for a single lead"""
        # Setup mocks
        mock_lead_repo = Mock()
        mock_lead_repo.add_message_to_history = AsyncMock()
        mock_lead_repo.update = AsyncMock()
        mock_lead_repo.schedule_follow_up = AsyncMock()
        
        mock_messaging = Mock()
        mock_messaging.send_sms = AsyncMock()
        mock_messaging.send_sms.return_value = True
        
        # Execute
        result = await process_follow_up(self.test_lead, mock_lead_repo, mock_messaging)
        
        # Verify
        assert result is True
        mock_messaging.send_sms.assert_called_once()
        mock_lead_repo.add_message_to_history.assert_called_once()
        mock_lead_repo.update.assert_called_once_with(self.test_lead.phone, {"follow_up_count": 2})
        mock_lead_repo.schedule_follow_up.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_follow_up_sms_failure(self):
        """Test follow-up processing when SMS fails"""
        # Setup mocks
        mock_lead_repo = Mock()
        mock_lead_repo.add_message_to_history = AsyncMock()
        mock_lead_repo.update = AsyncMock()
        mock_lead_repo.schedule_follow_up = AsyncMock()
        
        mock_messaging = Mock()
        mock_messaging.send_sms = AsyncMock()
        mock_messaging.send_sms.return_value = False
        
        # Execute
        result = await process_follow_up(self.test_lead, mock_lead_repo, mock_messaging)
        
        # Verify
        assert result is False
        mock_messaging.send_sms.assert_called_once()
        mock_lead_repo.add_message_to_history.assert_not_called()
        mock_lead_repo.update.assert_not_called()
        mock_lead_repo.schedule_follow_up.assert_not_called()

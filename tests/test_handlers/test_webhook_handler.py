import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from src.handlers.webhook_handler import lambda_handler, get_services


class TestWebhookHandler:
    """Test cases for webhook handler Lambda function"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.valid_webhook_event = {
            "body": json.dumps({
                "data": {
                    "event_type": "message.received",
                    "id": "test-event-123",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "payload": {
                        "from": {"phone_number": "+1234567890"},
                        "to": [{"phone_number": "+1987654321"}],
                        "text": "Hi, I'm looking for a 2 bedroom apartment",
                        "id": "msg-123"
                    }
                }
            })
        }
    
    @patch('src.handlers.webhook_handler.EventProcessor')
    @patch('src.handlers.webhook_handler.LeadProcessor')
    @patch('src.handlers.webhook_handler.DelayDetectionService')
    @patch('src.handlers.webhook_handler.OpenAIService')
    @patch('src.handlers.webhook_handler.TelnyxService')
    @patch('src.handlers.webhook_handler.LeadRepository')
    def test_lambda_handler_success(self, mock_lead_repo, mock_telnyx, mock_ai, mock_delay, mock_lead_processor, mock_event_processor):
        """Test successful webhook processing"""
        # Setup mocks
        mock_event_instance = Mock()
        mock_event_instance.validate_event = AsyncMock(return_value=True)
        mock_event_instance.process_event = AsyncMock()
        mock_event_instance.process_event.return_value = {
            "success": True,
            "response": "Thanks for your message!"
        }
        mock_event_processor.return_value = mock_event_instance
        
        # Execute
        result = lambda_handler(self.valid_webhook_event, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Message processed successfully"
        assert body["response"] == "Thanks for your message!"
        
        mock_event_instance.validate_event.assert_called_once()
        mock_event_instance.process_event.assert_called_once()
    
    @patch('src.handlers.webhook_handler.EventProcessor')
    @patch('src.handlers.webhook_handler.LeadProcessor')
    @patch('src.handlers.webhook_handler.DelayDetectionService')
    @patch('src.handlers.webhook_handler.OpenAIService')
    @patch('src.handlers.webhook_handler.TelnyxService')
    @patch('src.handlers.webhook_handler.LeadRepository')
    def test_lambda_handler_validation_failed(self, mock_lead_repo, mock_telnyx, mock_ai, mock_delay, mock_lead_processor, mock_event_processor):
        """Test webhook processing when validation fails"""
        # Setup mocks
        mock_event_instance = Mock()
        mock_event_instance.validate_event = AsyncMock(return_value=False)
        mock_event_processor.return_value = mock_event_instance
        
        # Execute
        result = lambda_handler(self.valid_webhook_event, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Event validation failed"
        
        mock_event_instance.validate_event.assert_called_once()
        mock_event_instance.process_event.assert_not_called()
    
    def test_lambda_handler_invalid_json(self):
        """Test webhook processing with invalid JSON"""
        # Execute with invalid JSON
        invalid_event = {"body": "invalid json"}
        result = lambda_handler(invalid_event, None)
        
        # Verify
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid JSON" in body["error"]
    
    def test_lambda_handler_agent_message_ignored(self):
        """Test that agent messages are ignored"""
        import os
        os.environ["AGENT_PHONE_NUMBER"] = "+1234567890"
        
        agent_webhook_event = {
            "body": json.dumps({
                "data": {
                    "event_type": "message.received",
                    "payload": {
                        "from": {"phone_number": "+1234567890"},
                        "to": [{"phone_number": "+1987654321"}],
                        "text": "Agent message"
                    }
                }
            })
        }
        
        result = lambda_handler(agent_webhook_event, None)
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Agent message ignored"
    
    def test_lambda_handler_telnyx_message_ignored(self):
        """Test that Telnyx messages are ignored"""
        import os
        os.environ["TELNYX_PHONE_NUMBER"] = "+1987654321"
        
        telnyx_webhook_event = {
            "body": json.dumps({
                "data": {
                    "event_type": "message.received",
                    "payload": {
                        "from": {"phone_number": "+1987654321"},
                        "to": [{"phone_number": "+1234567890"}],
                        "text": "Telnyx message"
                    }
                }
            })
        }
        
        result = lambda_handler(telnyx_webhook_event, None)
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Telnyx message ignored"

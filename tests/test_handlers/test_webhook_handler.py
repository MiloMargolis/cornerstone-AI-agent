import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from src.handlers.webhook_handler import lambda_handler, initialize_services


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
    
    @patch('src.handlers.webhook_handler.container')
    @patch('src.handlers.webhook_handler.ErrorHandler')
    def test_lambda_handler_success(self, mock_error_handler, mock_container):
        """Test successful webhook processing"""
        # Setup mocks
        mock_event_processor = Mock()
        mock_event_processor.validate_event = AsyncMock(return_value=True)
        mock_event_processor.process_event = AsyncMock()
        mock_event_processor.process_event.return_value = {
            "success": True,
            "response": "Thanks for your message!"
        }
        
        mock_container.resolve.return_value = mock_event_processor
        
        # Execute
        result = lambda_handler(self.valid_webhook_event, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Message processed successfully"
        assert body["response"] == "Thanks for your message!"
        
        mock_event_processor.validate_event.assert_called_once()
        mock_event_processor.process_event.assert_called_once()
    
    @patch('src.handlers.webhook_handler.container')
    @patch('src.handlers.webhook_handler.error_handler')
    def test_lambda_handler_validation_failed(self, mock_error_handler, mock_container):
        """Test webhook processing when validation fails"""
        # Reset global variables
        import src.handlers.webhook_handler as webhook_module
        webhook_module.event_processor = None
        webhook_module.error_handler = None
        
        # Setup mocks
        mock_event_processor = Mock()
        mock_event_processor.validate_event = AsyncMock(return_value=False)
        
        # Mock container methods
        mock_container.build_services = Mock()
        mock_container.resolve.return_value = mock_event_processor
        
        # Execute
        result = lambda_handler(self.valid_webhook_event, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Event validation failed"
        
        mock_event_processor.validate_event.assert_called_once()
        mock_event_processor.process_event.assert_not_called()
    
    @patch('src.handlers.webhook_handler.container')
    @patch('src.handlers.webhook_handler.error_handler')
    def test_lambda_handler_invalid_json(self, mock_error_handler, mock_container):
        """Test webhook processing with invalid JSON"""
        # Setup mocks
        mock_error_handler.handle_validation_error.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON"})
        }
        
        # Mock container methods
        mock_container.build_services = Mock()
        
        # Execute with invalid JSON
        invalid_event = {"body": "invalid json"}
        result = lambda_handler(invalid_event, None)
        
        # Verify
        assert result["statusCode"] == 400
        mock_error_handler.handle_validation_error.assert_called_once_with("Invalid JSON in webhook body")
    
    @patch('src.handlers.webhook_handler.container')
    @patch('src.handlers.webhook_handler.ErrorHandler')
    def test_lambda_handler_processing_error(self, mock_error_handler_class, mock_container):
        """Test webhook processing when processing fails"""
        # Reset global variables
        import src.handlers.webhook_handler as webhook_module
        webhook_module.event_processor = None
        webhook_module.error_handler = None
        
        # Setup mocks
        mock_event_processor = Mock()
        mock_event_processor.validate_event = AsyncMock(return_value=True)
        mock_event_processor.process_event = AsyncMock()
        mock_event_processor.process_event.side_effect = Exception("Processing error")
        
        mock_error_handler_instance = Mock()
        mock_error_handler_instance.handle_internal_error.return_value = {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal error"})
        }
        mock_error_handler_class.return_value = mock_error_handler_instance
        
        # Mock container methods
        mock_container.build_services = Mock()
        mock_container.resolve.return_value = mock_event_processor
        
        # Execute
        result = lambda_handler(self.valid_webhook_event, None)
        
        # Verify
        assert result["statusCode"] == 500
        mock_error_handler_instance.handle_internal_error.assert_called_once_with("Processing error")

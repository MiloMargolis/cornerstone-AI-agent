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
    @patch('src.handlers.webhook_handler.ErrorHandler')
    def test_lambda_handler_validation_failed(self, mock_error_handler, mock_container):
        """Test webhook processing when validation fails"""
        # Setup mocks
        mock_event_processor = Mock()
        mock_event_processor.validate_event = AsyncMock(return_value=False)
        
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
    @patch('src.handlers.webhook_handler.ErrorHandler')
    def test_lambda_handler_ignored_event_type(self, mock_error_handler, mock_container):
        """Test webhook processing when event type is ignored"""
        # Setup event with non-message event
        ignored_event = {
            "body": json.dumps({
                "data": {
                    "event_type": "message.sent",
                    "payload": {
                        "from": {"phone_number": "+1234567890"},
                        "to": [{"phone_number": "+1987654321"}],
                        "text": "Test message"
                    }
                }
            })
        }
        
        mock_event_processor = Mock()
        mock_container.resolve.return_value = mock_event_processor
        
        # Execute
        result = lambda_handler(ignored_event, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Event ignored"
        
        mock_event_processor.validate_event.assert_not_called()
        mock_event_processor.process_event.assert_not_called()
    
    @patch('src.handlers.webhook_handler.container')
    @patch('src.handlers.webhook_handler.ErrorHandler')
    @patch.dict('os.environ', {'AGENT_PHONE_NUMBER': '+1987654321'})
    def test_lambda_handler_agent_message_ignored(self, mock_error_handler, mock_container):
        """Test webhook processing when message is from agent"""
        # Setup event with agent phone number
        agent_event = {
            "body": json.dumps({
                "data": {
                    "event_type": "message.received",
                    "payload": {
                        "from": {"phone_number": "+1987654321"},  # Agent phone
                        "to": [{"phone_number": "+1234567890"}],
                        "text": "Agent message"
                    }
                }
            })
        }
        
        mock_event_processor = Mock()
        mock_container.resolve.return_value = mock_event_processor
        
        # Execute
        result = lambda_handler(agent_event, None)
        
        # Verify
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["message"] == "Agent message ignored"
        
        mock_event_processor.validate_event.assert_not_called()
        mock_event_processor.process_event.assert_not_called()
    
    @patch('src.handlers.webhook_handler.container')
    @patch('src.handlers.webhook_handler.ErrorHandler')
    def test_lambda_handler_invalid_json(self, mock_error_handler, mock_container):
        """Test webhook processing with invalid JSON"""
        # Setup mocks
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        mock_error_handler_instance.handle_validation_error.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON"})
        }
        
        # Execute with invalid JSON
        invalid_event = {"body": "invalid json"}
        result = lambda_handler(invalid_event, None)
        
        # Verify
        assert result["statusCode"] == 400
        mock_error_handler_instance.handle_validation_error.assert_called_once_with("Invalid JSON in webhook body")
    
    @patch('src.handlers.webhook_handler.container')
    @patch('src.handlers.webhook_handler.ErrorHandler')
    def test_lambda_handler_invalid_webhook_data(self, mock_error_handler, mock_container):
        """Test webhook processing with invalid webhook data"""
        # Setup mocks
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        mock_error_handler_instance.handle_validation_error.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid webhook data"})
        }
        
        # Execute with invalid webhook data
        invalid_webhook_event = {
            "body": json.dumps({
                "data": {
                    "event_type": "message.received",
                    "payload": {
                        # Missing required fields
                    }
                }
            })
        }
        
        result = lambda_handler(invalid_webhook_event, None)
        
        # Verify
        assert result["statusCode"] == 400
        mock_error_handler_instance.handle_validation_error.assert_called_once()
    
    @patch('src.handlers.webhook_handler.container')
    @patch('src.handlers.webhook_handler.ErrorHandler')
    def test_lambda_handler_processing_error(self, mock_error_handler, mock_container):
        """Test webhook processing when processing fails"""
        # Setup mocks
        mock_event_processor = Mock()
        mock_event_processor.validate_event = AsyncMock(return_value=True)
        mock_event_processor.process_event = AsyncMock()
        mock_event_processor.process_event.side_effect = Exception("Processing error")
        
        mock_error_handler_instance = Mock()
        mock_error_handler.return_value = mock_error_handler_instance
        mock_error_handler_instance.handle_internal_error.return_value = {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal error"})
        }
        
        mock_container.resolve.return_value = mock_event_processor
        
        # Execute
        result = lambda_handler(self.valid_webhook_event, None)
        
        # Verify
        assert result["statusCode"] == 500
        mock_error_handler_instance.handle_internal_error.assert_called_once_with("Processing error")
    
    @patch('src.handlers.webhook_handler.container')
    def test_initialize_services(self, mock_container):
        """Test service initialization"""
        # Execute
        initialize_services()
        
        # Verify
        mock_container.build_services.assert_called_once()

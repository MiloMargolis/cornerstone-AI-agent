import pytest
import json
from unittest.mock import patch
from src.middleware.error_handler import ErrorHandler


class TestErrorHandler:
    """Test cases for ErrorHandler middleware"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.error_handler = ErrorHandler()
    
    def test_handle_validation_error(self):
        """Test handling validation errors"""
        message = "Invalid input data"
        details = {"field": "email", "issue": "invalid format"}
        
        result = self.error_handler.handle_validation_error(message, details)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["error"] == "Validation Error"
        assert body["message"] == message
        assert body["type"] == "VALIDATION_ERROR"
        assert body["details"] == details
        assert "timestamp" in body
    
    def test_handle_validation_error_no_details(self):
        """Test handling validation errors without details"""
        message = "Invalid input data"
        
        result = self.error_handler.handle_validation_error(message)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["error"] == "Validation Error"
        assert body["message"] == message
        assert "details" not in body
    
    def test_handle_authentication_error(self):
        """Test handling authentication errors"""
        message = "Invalid credentials"
        
        result = self.error_handler.handle_authentication_error(message)
        
        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert body["error"] == "Authentication Error"
        assert body["message"] == message
        assert body["type"] == "AUTHENTICATION_ERROR"
    
    def test_handle_authentication_error_default_message(self):
        """Test handling authentication errors with default message"""
        result = self.error_handler.handle_authentication_error()
        
        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert body["message"] == "Authentication failed"
    
    def test_handle_authorization_error(self):
        """Test handling authorization errors"""
        message = "Insufficient permissions"
        
        result = self.error_handler.handle_authorization_error(message)
        
        assert result["statusCode"] == 403
        body = json.loads(result["body"])
        assert body["error"] == "Authorization Error"
        assert body["message"] == message
        assert body["type"] == "AUTHORIZATION_ERROR"
    
    def test_handle_authorization_error_default_message(self):
        """Test handling authorization errors with default message"""
        result = self.error_handler.handle_authorization_error()
        
        assert result["statusCode"] == 403
        body = json.loads(result["body"])
        assert body["message"] == "Access denied"
    
    def test_handle_not_found_error(self):
        """Test handling not found errors"""
        resource = "User"
        message = "User not found in database"
        
        result = self.error_handler.handle_not_found_error(resource, message)
        
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["error"] == "Not Found"
        assert body["message"] == message
        assert body["type"] == "NOT_FOUND_ERROR"
    
    def test_handle_not_found_error_default_message(self):
        """Test handling not found errors with default message"""
        resource = "User"
        
        result = self.error_handler.handle_not_found_error(resource)
        
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["message"] == "User not found"
    
    def test_handle_internal_error(self):
        """Test handling internal server errors"""
        message = "Database connection failed"
        error_id = "err-12345"
        
        result = self.error_handler.handle_internal_error(message, error_id)
        
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["error"] == "Internal Server Error"
        assert body["message"] == "An unexpected error occurred"
        assert body["type"] == "INTERNAL_ERROR"
        assert body["error_id"] == error_id
    
    def test_handle_internal_error_no_error_id(self):
        """Test handling internal server errors without error ID"""
        message = "Database connection failed"
        
        result = self.error_handler.handle_internal_error(message)
        
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["error"] == "Internal Server Error"
        assert "error_id" not in body
    
    def test_handle_service_unavailable_error(self):
        """Test handling service unavailable errors"""
        service = "Payment Gateway"
        message = "Payment service is down"
        
        result = self.error_handler.handle_service_unavailable_error(service, message)
        
        assert result["statusCode"] == 503
        body = json.loads(result["body"])
        assert body["error"] == "Service Unavailable"
        assert body["message"] == message
        assert body["type"] == "SERVICE_UNAVAILABLE_ERROR"
    
    def test_handle_service_unavailable_error_default_message(self):
        """Test handling service unavailable errors with default message"""
        service = "Payment Gateway"
        
        result = self.error_handler.handle_service_unavailable_error(service)
        
        assert result["statusCode"] == 503
        body = json.loads(result["body"])
        assert body["message"] == "Payment Gateway service is temporarily unavailable"
    
    def test_handle_rate_limit_error(self):
        """Test handling rate limit errors"""
        retry_after = 60
        
        result = self.error_handler.handle_rate_limit_error(retry_after)
        
        assert result["statusCode"] == 429
        assert result["headers"]["Retry-After"] == "60"
        body = json.loads(result["body"])
        assert body["error"] == "Rate Limit Exceeded"
        assert body["message"] == "Too many requests"
        assert body["type"] == "RATE_LIMIT_ERROR"
        assert body["retry_after"] == retry_after
    
    def test_handle_rate_limit_error_no_retry_after(self):
        """Test handling rate limit errors without retry after"""
        result = self.error_handler.handle_rate_limit_error()
        
        assert result["statusCode"] == 429
        assert "headers" not in result
        body = json.loads(result["body"])
        assert body["error"] == "Rate Limit Exceeded"
        assert "retry_after" not in body
    
    def test_handle_database_error(self):
        """Test handling database errors"""
        operation = "INSERT"
        error = Exception("Connection timeout")
        
        result = self.error_handler.handle_database_error(operation, error)
        
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["error"] == "Database Error"
        assert body["message"] == "Database operation failed: INSERT"
        assert body["type"] == "DATABASE_ERROR"
    
    def test_handle_external_api_error(self):
        """Test handling external API errors"""
        service = "Stripe"
        operation = "create_payment"
        error = Exception("API timeout")
        
        result = self.error_handler.handle_external_api_error(service, operation, error)
        
        assert result["statusCode"] == 502
        body = json.loads(result["body"])
        assert body["error"] == "External API Error"
        assert body["message"] == "Stripe API operation failed: create_payment"
        assert body["type"] == "EXTERNAL_API_ERROR"
    
    def test_handle_webhook_processing_error(self):
        """Test handling webhook processing errors"""
        event_type = "message.received"
        error = Exception("Invalid payload")
        
        result = self.error_handler.handle_webhook_processing_error(event_type, error)
        
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["error"] == "Webhook Processing Error"
        assert body["message"] == "Failed to process message.received webhook"
        assert body["type"] == "WEBHOOK_PROCESSING_ERROR"
    
    @patch('src.middleware.error_handler.logging')
    def test_log_error(self, mock_logging):
        """Test logging errors"""
        error = Exception("Test error")
        context = {"user_id": "123", "action": "login"}
        
        self.error_handler.log_error(error, context)
        
        mock_logging.getLogger.return_value.error.assert_called_once()
        call_args = mock_logging.getLogger.return_value.error.call_args
        assert "Test error" in call_args[0][0]
        assert call_args[1]["extra"]["error_type"] == "Exception"
        assert call_args[1]["extra"]["context"] == context
        assert call_args[1]["exc_info"] is True
    
    @patch('src.middleware.error_handler.logging')
    def test_log_warning(self, mock_logging):
        """Test logging warnings"""
        message = "Warning message"
        context = {"field": "email"}
        
        self.error_handler.log_warning(message, context)
        
        mock_logging.getLogger.return_value.warning.assert_called_once()
        call_args = mock_logging.getLogger.return_value.warning.call_args
        assert call_args[0][0] == message
        assert call_args[1]["extra"]["context"] == context
    
    @patch('src.middleware.error_handler.logging')
    def test_log_info(self, mock_logging):
        """Test logging info messages"""
        message = "Info message"
        context = {"user_id": "123"}
        
        self.error_handler.log_info(message, context)
        
        mock_logging.getLogger.return_value.info.assert_called_once()
        call_args = mock_logging.getLogger.return_value.info.call_args
        assert call_args[0][0] == message
        assert call_args[1]["extra"]["context"] == context
    
    def test_timestamp_format(self):
        """Test that timestamps are in ISO format"""
        result = self.error_handler.handle_validation_error("Test error")
        body = json.loads(result["body"])
        
        # Check that timestamp is a valid ISO format string
        from datetime import datetime
        try:
            datetime.fromisoformat(body["timestamp"])
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

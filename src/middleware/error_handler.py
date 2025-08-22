import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime


class ErrorHandler:
    """Centralized error handling for the application"""
    
    def __init__(self):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def handle_validation_error(self, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle validation errors (400 Bad Request)"""
        error_response = {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Validation Error",
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "type": "VALIDATION_ERROR"
            })
        }
        
        if details:
            error_response["body"] = json.dumps({
                **json.loads(error_response["body"]),
                "details": details
            })
        
        self.logger.warning(f"Validation error: {message}", extra={"details": details})
        return error_response
    
    def handle_authentication_error(self, message: str = "Authentication failed") -> Dict[str, Any]:
        """Handle authentication errors (401 Unauthorized)"""
        error_response = {
            "statusCode": 401,
            "body": json.dumps({
                "error": "Authentication Error",
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "type": "AUTHENTICATION_ERROR"
            })
        }
        
        self.logger.warning(f"Authentication error: {message}")
        return error_response
    
    def handle_authorization_error(self, message: str = "Access denied") -> Dict[str, Any]:
        """Handle authorization errors (403 Forbidden)"""
        error_response = {
            "statusCode": 403,
            "body": json.dumps({
                "error": "Authorization Error",
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "type": "AUTHORIZATION_ERROR"
            })
        }
        
        self.logger.warning(f"Authorization error: {message}")
        return error_response
    
    def handle_not_found_error(self, resource: str, message: Optional[str] = None) -> Dict[str, Any]:
        """Handle not found errors (404 Not Found)"""
        if not message:
            message = f"{resource} not found"
        
        error_response = {
            "statusCode": 404,
            "body": json.dumps({
                "error": "Not Found",
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "type": "NOT_FOUND_ERROR"
            })
        }
        
        self.logger.info(f"Not found error: {message}")
        return error_response
    
    def handle_internal_error(self, message: str, error_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle internal server errors (500 Internal Server Error)"""
        error_response = {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.now().isoformat(),
                "type": "INTERNAL_ERROR"
            })
        }
        
        if error_id:
            error_response["body"] = json.dumps({
                **json.loads(error_response["body"]),
                "error_id": error_id
            })
        
        self.logger.error(f"Internal error: {message}", extra={"error_id": error_id})
        return error_response
    
    def handle_service_unavailable_error(self, service: str, message: Optional[str] = None) -> Dict[str, Any]:
        """Handle service unavailable errors (503 Service Unavailable)"""
        if not message:
            message = f"{service} service is temporarily unavailable"
        
        error_response = {
            "statusCode": 503,
            "body": json.dumps({
                "error": "Service Unavailable",
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "type": "SERVICE_UNAVAILABLE_ERROR"
            })
        }
        
        self.logger.error(f"Service unavailable: {message}")
        return error_response
    
    def handle_rate_limit_error(self, retry_after: Optional[int] = None) -> Dict[str, Any]:
        """Handle rate limit errors (429 Too Many Requests)"""
        error_response = {
            "statusCode": 429,
            "body": json.dumps({
                "error": "Rate Limit Exceeded",
                "message": "Too many requests",
                "timestamp": datetime.now().isoformat(),
                "type": "RATE_LIMIT_ERROR"
            })
        }
        
        if retry_after:
            error_response["headers"] = {"Retry-After": str(retry_after)}
            error_response["body"] = json.dumps({
                **json.loads(error_response["body"]),
                "retry_after": retry_after
            })
        
        self.logger.warning("Rate limit exceeded")
        return error_response
    
    def handle_database_error(self, operation: str, error: Exception) -> Dict[str, Any]:
        """Handle database-related errors"""
        error_response = {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Database Error",
                "message": f"Database operation failed: {operation}",
                "timestamp": datetime.now().isoformat(),
                "type": "DATABASE_ERROR"
            })
        }
        
        self.logger.error(f"Database error during {operation}: {str(error)}")
        return error_response
    
    def handle_external_api_error(self, service: str, operation: str, error: Exception) -> Dict[str, Any]:
        """Handle external API errors"""
        error_response = {
            "statusCode": 502,
            "body": json.dumps({
                "error": "External API Error",
                "message": f"{service} API operation failed: {operation}",
                "timestamp": datetime.now().isoformat(),
                "type": "EXTERNAL_API_ERROR"
            })
        }
        
        self.logger.error(f"External API error - {service} {operation}: {str(error)}")
        return error_response
    
    def handle_webhook_processing_error(self, event_type: str, error: Exception) -> Dict[str, Any]:
        """Handle webhook processing errors"""
        error_response = {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Webhook Processing Error",
                "message": f"Failed to process {event_type} webhook",
                "timestamp": datetime.now().isoformat(),
                "type": "WEBHOOK_PROCESSING_ERROR"
            })
        }
        
        self.logger.error(f"Webhook processing error for {event_type}: {str(error)}")
        return error_response
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log an error with optional context"""
        self.logger.error(
            f"Error: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "context": context or {}
            },
            exc_info=True
        )
    
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log a warning with optional context"""
        self.logger.warning(
            message,
            extra={"context": context or {}}
        )
    
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log an info message with optional context"""
        self.logger.info(
            message,
            extra={"context": context or {}}
        )

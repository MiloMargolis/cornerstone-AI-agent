import asyncio
import json
from typing import Dict, Any
from dotenv import load_dotenv

from src.core.container import container
from src.core.event_processor import EventProcessor
from src.models.webhook import WebhookEvent
from src.middleware.error_handler import ErrorHandler


# Initialize the service container
def initialize_services():
    """Initialize all services and dependencies"""
    container.build_services()


# Global handler instance
event_processor = None
error_handler = None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for processing Telnyx webhook events with dependency injection
    """
    global event_processor, error_handler
    
    # Initialize services if not already done
    if event_processor is None:
        initialize_services()
        event_processor = container.resolve(EventProcessor)
        error_handler = ErrorHandler()
    
    try:
        # Parse the incoming webhook
        body = json.loads(event.get("body", "{}"))
        print(f"Received webhook: {json.dumps(body, indent=2)}")
        
        # Extract webhook data
        webhook_data = body.get("data", {})
        
        # Create WebhookEvent from raw data
        try:
            webhook_event = WebhookEvent.from_telnyx_webhook(webhook_data)
        except ValueError as e:
            print(f"Invalid webhook data: {e}")
            return error_handler.handle_validation_error(str(e))
        
        # Validate the event
        if not asyncio.run(event_processor.validate_event(webhook_event)):
            print(f"Event validation failed for event type: {webhook_event.event_type}")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Event validation failed"})
            }
        
        # We only care about incoming messages
        if not webhook_event.is_message_received():
            print(f"Ignoring event type: {webhook_event.event_type}")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Event ignored"})
            }
        
        # Check if this message is from the agent (ignore if so)
        import os
        agent_phone = os.getenv("AGENT_PHONE_NUMBER")
        if agent_phone and webhook_event.is_from_agent(agent_phone):
            print(f"Ignoring message from agent: {webhook_event.payload.from_number}")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Agent message ignored"})
            }
        
        # Process the event
        result = asyncio.run(event_processor.process_event(webhook_event))
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Message processed successfully",
                "response": result.get("response", "")
            })
        }
        
    except json.JSONDecodeError as e:
        print(f"Error parsing webhook JSON: {e}")
        return error_handler.handle_validation_error("Invalid JSON in webhook body")
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return error_handler.handle_internal_error(str(e))


# For local testing
if __name__ == "__main__":
    # Test event structure
    test_event = {
        "body": json.dumps({
            "data": {
                "event_type": "message.received",
                "payload": {
                    "from": {"phone_number": "+1234567890"},
                    "to": [{"phone_number": "+1987654321"}],
                    "text": "Hi, I'm looking for a 2 bedroom apartment",
                },
            }
        })
    }
    
    print("Testing webhook handler locally...")
    print("Loading local .env")
    load_dotenv()
    
    # Initialize services
    initialize_services()
    
    # Test the handler
    result = lambda_handler(test_event, None)
    print(f"Result: {result}")

import asyncio
import json
from typing import Dict, Any
from dotenv import load_dotenv

from services.database.lead_repository import LeadRepository
from services.messaging.telnyx_service import TelnyxService
from services.ai.openai_service import OpenAIService
from services.delay_detection.delay_detection_service import DelayDetectionService
from core.lead_processor import LeadProcessor
from core.event_processor import EventProcessor
from models.webhook import WebhookEvent
from middleware.error_handler import ErrorHandler


# Simple service instances - created once per Lambda container
_services_initialized = False
_lead_processor = None
_event_processor = None


def get_services():
    """Get or create service instances (singleton pattern)"""
    global _services_initialized, _lead_processor, _event_processor
    
    if not _services_initialized:
        print("[INIT] Creating service instances")
        
        # Create services directly
        lead_repository = LeadRepository()
        messaging_service = TelnyxService()
        ai_service = OpenAIService()
        delay_detection_service = DelayDetectionService()
        
        # Create processors
        _lead_processor = LeadProcessor(
            lead_repository=lead_repository,
            messaging_service=messaging_service,
            ai_service=ai_service,
            delay_detection_service=delay_detection_service
        )
        
        _event_processor = EventProcessor(lead_processor=_lead_processor)
        _services_initialized = True
        
        print("[INIT] Services created successfully")
    
    return _event_processor


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simple Lambda handler for processing Telnyx webhook events
    """
    # Get services (created once per container)
    event_processor = get_services()
    error_handler = ErrorHandler()

    try:
        # Parse the incoming webhook
        body = json.loads(event.get("body", "{}"))
        
        # Extract webhook data
        webhook_data = body.get("data", {})

        # Create WebhookEvent from raw data
        try:
            webhook_event = WebhookEvent.from_telnyx_webhook(webhook_data)
            webhook_event_data = {
                "event_type": webhook_event.event_type.value,
                "from_number": webhook_event.payload.from_number,
                "to_numbers": webhook_event.payload.to_numbers,
                "text": webhook_event.payload.text,
            }
        except ValueError as e:
            print(f"Invalid webhook data: {e}")
            return error_handler.handle_validation_error(str(e))

        # Validate the event
        if not asyncio.run(event_processor.validate_event(webhook_event)):
            print(f"Event validation failed for event type: {webhook_event.event_type.value}")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Event validation failed"}),
            }

        # We only care about incoming messages
        if not webhook_event.is_message_received():
            print(f"Ignoring event type: {webhook_event.event_type.value}")
            return {"statusCode": 200, "body": json.dumps({"message": "Event ignored"})}

        # Check if this message is from the agent or Telnyx number (ignore if so)
        import os
        agent_phone = os.getenv("AGENT_PHONE_NUMBER")
        telnyx_phone = os.getenv("TELNYX_PHONE_NUMBER")

        if agent_phone and webhook_event.is_from_agent(agent_phone):
            print(f"Ignoring message from agent: {webhook_event.payload.from_number}")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Agent message ignored"}),
            }

        if telnyx_phone and webhook_event.payload.from_number == telnyx_phone:
            print(f"Ignoring message from Telnyx number: {webhook_event.payload.from_number}")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Telnyx message ignored"}),
            }

        # Process the event
        result = asyncio.run(event_processor.process_event(webhook_event))

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Message processed successfully",
                "response": result.get("response", ""),
            }),
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

    # Test the handler
    result = lambda_handler(test_event, None)
    print(f"Result: {result}")

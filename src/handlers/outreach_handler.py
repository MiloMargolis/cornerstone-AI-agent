import re
import asyncio
from typing import Dict, Any
import json

from services.database.lead_repository import LeadRepository
from services.messaging.telnyx_service import TelnyxService
from models.lead import Lead
from middleware.error_handler import ErrorHandler


# Simple service instances - created once per Lambda container
_services_initialized = False
_lead_repository = None
_messaging_service = None


def get_services():
    """Get or create service instances (singleton pattern)"""
    global _services_initialized, _lead_repository, _messaging_service
    
    if not _services_initialized:
        print("[INIT] Creating outreach service instances")
        
        # Create services directly
        _lead_repository = LeadRepository()
        _messaging_service = TelnyxService()
        _services_initialized = True
        
        print("[INIT] Outreach services created successfully")
    
    return _lead_repository, _messaging_service


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for the outreach handler
    """
    try:
        # Get services (created once per container)
        lead_repository, messaging_service = get_services()
        error_handler = ErrorHandler()

        # Validate input
        if not event or "phone_number" not in event:
            return error_handler.handle_validation_error("Missing required field: phone_number")
        
        if not event or "name" not in event:
            return error_handler.handle_validation_error("Missing required field: name")

        phone_number = event["phone_number"]
        name = event["name"]

        # Validate phone number format
        normalized_phone_number = validate_phone_number(phone_number)
        if not normalized_phone_number:
            return error_handler.handle_validation_error("Invalid phone number format")

        # Check if phone number already exists
        existing_lead = asyncio.run(lead_repository.get_by_phone(normalized_phone_number))
        if existing_lead:
            return error_handler.handle_validation_error("Phone number already exists in the database")

        # Create a new lead
        lead = Lead(phone=normalized_phone_number, name=name)
        created_lead = asyncio.run(lead_repository.create(lead))
        
        if not created_lead:
            return error_handler.handle_internal_error("Failed to create lead record")

        # Send initial outreach message
        success = asyncio.run(send_initial_outreach_message(created_lead, normalized_phone_number, lead_repository, messaging_service))
        if success:
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Initial outreach message sent successfully"})
            }
        else:
            return error_handler.handle_internal_error("Failed to send initial outreach message")

    except Exception as e:
        print(f"Error in outreach handler: {e}")
        return error_handler.handle_internal_error("Internal server error")


def validate_phone_number(phone: str) -> str | None:
    """
    Validate and normalize a US phone number.
    Accepts formatted numbers and optional +1 country code.
    Always returns in +1XXXXXXXXXX format.
    Returns None if invalid.
    """
    digits = re.sub(r"\D", "", phone)  # remove all non-digits

    if len(digits) == 10:  # no country code
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):  # already has country code
        return "+1" + digits[1:]
    return None


def extract_first_name(full_name: str | None) -> str:
    """
    Extract a clean first name from a provided name string.
    - Trims whitespace
    - Splits on whitespace and uses the first token
    - Normalizes casing (Title case)
    - Strips non-name punctuation except hyphens/apostrophes
    """
    if not full_name:
        return ""

    # Split on whitespace and take the first non-empty part
    parts = [part for part in re.split(r"\s+", full_name.strip()) if part]
    if not parts:
        return ""

    raw_first = parts[0]
    # Keep letters plus common name punctuation (hyphen, apostrophe)
    cleaned_first = re.sub(r"[^A-Za-z'\-]", "", raw_first)
    if not cleaned_first:
        return ""

    return cleaned_first[:1].upper() + cleaned_first[1:].lower()


async def send_initial_outreach_message(
    lead: Lead, 
    phone_number: str, 
    lead_repository: LeadRepository,
    messaging_service: TelnyxService
) -> bool:
    """
    Send the initial outreach message to the phone number.
    Returns True if successful, False otherwise.
    """
    try:
        first_name = extract_first_name(lead.name)
        greeting = f"Hi {first_name}, " if first_name else "Hi, "
        response = (
            f"{greeting}my name is Josh from Cornerstone Real Estate, I saw you were looking for apartments in Boston. "
            "To get started, what is your price range and preferred neighborhoods?"
        )

        success = await messaging_service.send_sms(phone_number, response)
        if success:
            # Update message history with response
            await lead_repository.add_message_to_history(phone_number, response, "ai")
            print(f"AI response sent to {phone_number}: {response}")
            return True
        else:
            print(f"Failed to send AI response to {phone_number}")
            return False
    except Exception as e:
        print(f"Error sending initial outreach message: {e}")
        return False


# For local testing
if __name__ == "__main__":
    print("Testing outreach handler locally...")
    
    test_event = {
        "phone_number": "+1234567890",
        "name": "John Doe"
    }
    
    result = lambda_handler(test_event, None)
    print(f"Result: {result}")

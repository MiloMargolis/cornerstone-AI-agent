from typing import Dict, Any
import json
import re

from utils.supabase_client import SupabaseClient
from utils.telnyx_client import TelnyxClient

supabase_client = SupabaseClient()
telnyx_client = TelnyxClient()


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


def check_if_phone_number_exists(phone_number: str) -> bool:
    """
    Check if the phone number exists in the database.
    """
    try:
        return supabase_client.get_lead_by_phone(phone_number) is not None
    except Exception as e:
        print(f"Error checking if phone number exists: {e}")
        raise Exception(f"Failed to check phone number in database: {str(e)}")


def call_create_lead(phone_number: str, name: str, initial_message: str):
    """
    Create a new lead in the database.
    """
    try:
        lead = supabase_client.create_lead(
            phone=phone_number, name=name, initial_message=initial_message
        )
        if not lead:
            raise Exception("Failed to create lead record")
        return lead
    except Exception as e:
        print(f"Error creating lead: {e}")
        raise Exception(f"Failed to create lead record: {str(e)}")


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


def send_initial_outreach_message(lead: Dict[str, Any], phone_number: str) -> bool:
    """
    Send the initial outreach message to the phone number.
    Returns True if successful, False otherwise.
    """
    try:
        missing_fields = supabase_client.get_missing_fields(lead)
        needs_tour_availability = supabase_client.needs_tour_availability(lead)
        missing_optional = supabase_client.get_missing_optional_fields(lead)

        name = lead.get("name")
        first_name = extract_first_name(name)
        greeting = f"Hi {first_name}, " if first_name else "Hi, "
        response = (
            f"{greeting}my name is Josh from Cornerstone Real Estate, I saw you were looking for apartments in Boston. "
            "To get started, what is your price range and preferred neighborhoods?"
        )

        success = telnyx_client.send_sms(phone_number, response)
        if success:
            # Update message history with response
            supabase_client.add_message_to_history(phone_number, response, "ai")
            print(f"AI response sent to {phone_number}: {response}")
            return True
        else:
            print(f"Failed to send AI response to {phone_number}")
            return False
    except Exception as e:
        print(f"Error sending initial outreach message: {e}")
        return False


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for the outreach handler.
    """
    try:
        # Validate input
        if not event or "phone_number" not in event:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required field: phone_number"}),
            }
        if not event or "name" not in event:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required field: name"}),
            }

        phone_number = event["phone_number"]
        name = event["name"]

        # Validate phone number format
        normalized_phone_number = validate_phone_number(phone_number)
        if not normalized_phone_number:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid phone number format"}),
            }

        # Check if phone number already exists
        if check_if_phone_number_exists(normalized_phone_number):
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"error": "Phone number already exists in the database"}
                ),
            }

        # Create a new lead
        lead = call_create_lead(
            phone_number=normalized_phone_number, name=name, initial_message=""
        )

        # Send initial outreach message
        if send_initial_outreach_message(lead, phone_number):
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {"message": "Initial outreach message sent successfully"}
                ),
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {"error": "Failed to send initial outreach message"}
                ),
            }

    except KeyError as e:
        print(f"Missing required field in event: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Missing required field: {str(e)}"}),
        }
    except ValueError as e:
        print(f"Invalid value in request: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Invalid value: {str(e)}"}),
        }
    except Exception as e:
        print(f"Error in outreach handler: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }

import json
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Import our utility classes
from utils.supabase_client import SupabaseClient
from utils.openai_client import OpenAIClient

if os.getenv("MOCK_TELNX", "0") == "0":
    from utils.telnyx_client import TelnyxClient
else:
    from utils.telnyx_client import MockTelnyxClient as TelnyxClient
from utils.delay_detector import DelayDetector
from config.follow_up_config import FOLLOW_UP_SCHEDULE
from utils.constants import REQUIRED_FIELDS, OPTIONAL_FIELDS


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for processing Telnyx webhook events
    """

    # Parse the incoming webhook
    try:
        # Get the request body
        body = json.loads(event.get("body", "{}"))
        print(f"Received webhook: {json.dumps(body, indent=2)}")

        # Extract webhook data
        webhook_data = body.get("data", {})
        event_type = webhook_data.get("event_type")

        # We only care about incoming messages
        if event_type != "message.received":
            print(f"Ignoring event type: {event_type}")
            return {"statusCode": 200, "body": json.dumps({"message": "Event ignored"})}

        # Extract message details
        payload = webhook_data.get("payload", {})
        from_number = payload.get("from", {}).get("phone_number")
        # Fix: 'to' is a list, get the first element
        to_list = payload.get("to", [])
        to_number = to_list[0].get("phone_number") if to_list else None
        message_text = payload.get("text")

        if not from_number or not message_text:
            print("Missing required message data")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required message data"}),
            }

        # Check if this message is from the agent (ignore if so)
        agent_phone = os.getenv("AGENT_PHONE_NUMBER")
        if agent_phone and from_number == agent_phone:
            print(f"Ignoring message from agent: {from_number}")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Agent message ignored"}),
            }

        # Process the lead message
        response = process_lead_message(from_number, message_text)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Message processed successfully", "response": response}
            ),
        }

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def _generate_delay_response(delay_info: Dict[str, Any]) -> str:
    # Generate appropriate delay response
    delay_days = delay_info["delay_days"]
    if delay_days == 1:
        time_phrase = "tomorrow"
    elif delay_days <= 7:
        time_phrase = f"in {delay_days} days"
    elif delay_days <= 30:
        weeks = delay_days // 7
        time_phrase = f"in {weeks} week{'s' if weeks > 1 else ''}"
    else:
        months = delay_days // 30
        time_phrase = f"in {months} month{'s' if months > 1 else ''}"

    ai_response = f"No problem! I'll reach out {time_phrase}. Feel free to message me anytime if you have questions before then."

    return ai_response


def process_lead_message(lead_phone: str, message: str) -> str:
    """
    Process an incoming message from a lead
    """
    try:
        # Initialize clients
        supabase_client = SupabaseClient()
        openai_client = OpenAIClient()
        telnyx_client = TelnyxClient()
        delay_detector = DelayDetector()

        # Get or create lead record
        lead = supabase_client.get_lead_by_phone(lead_phone)

        if not lead:
            # Create new lead
            print(f"Creating new lead for phone: {lead_phone}")
            lead = supabase_client.create_lead(
                phone=lead_phone, initial_message=message
            )
            if not lead:
                raise Exception("Failed to create lead record")

        # Extract any new information from the message
        extracted_info = openai_client.extract_lead_info(message, lead)

        # Update lead with extracted information
        if extracted_info:
            print(f"[DEBUG] Extracted info: {extracted_info}")
            updated_lead = supabase_client.update_lead(lead_phone, extracted_info)
            if updated_lead:
                print(f"[DEBUG] Lead updated successfully. Current lead data:")
                for field in [
                    "move_in_date",
                    "price",
                    "beds",
                    "baths",
                    "location",
                    "amenities",
                    "tour_availability",
                    "tour_ready",
                ]:
                    print(f"  {field}: '{updated_lead.get(field, 'EMPTY')}'")
            else:
                print(
                    f"[ERROR] Failed to update lead with extracted info: {extracted_info}"
                )
        else:
            print(f"[DEBUG] No information extracted from message: '{message}'")

        # Update message history
        supabase_client.add_message_to_history(lead_phone, message, "lead")

        # Refresh lead data to include the updated conversation history
        lead = supabase_client.get_lead_by_phone(lead_phone)

        # Check if conversation is already complete (tour_ready = True)
        if lead.get("tour_ready", False):
            # Conversation is complete - stay completely silent
            print(
                f"Lead {lead_phone} is tour_ready - staying silent (no response sent)"
            )
            return "SILENT_TOUR_READY"  # Return early, no SMS sent

        # Check if tour availability was just provided - trigger manager response
        # This should happen BEFORE delay detection to avoid false positives
        elif (
            extracted_info.get("tour_availability")
            and not lead.get("tour_availability", "").strip()
        ):
            # Set tour_ready to true
            print(
                f"Lead {lead_phone} provided tour availability - marking as tour_ready"
            )
            supabase_client.set_tour_ready(lead_phone)

            # Refresh lead data after setting tour_ready
            lead = supabase_client.get_lead_by_phone(lead_phone)

            # Send notification to agent
            agent_phone = os.getenv("AGENT_PHONE_NUMBER")
            if agent_phone:
                lead_name = lead.get("name", "").strip()
                name_part = lead_name if lead_name else "Lead"
                agent_message = (
                    f"{name_part} with phone number {lead_phone} is ready for a tour"
                )

                agent_sms_success = telnyx_client.send_sms(agent_phone, agent_message)
                if agent_sms_success:
                    print(f"Agent notification sent to {agent_phone}: {agent_message}")
                else:
                    print(f"Failed to send agent notification to {agent_phone}")
            else:
                print("No AGENT_PHONE_NUMBER configured - skipping agent notification")

            ai_response = "Perfect! I have all the information I need. I'll get my teammate to set up an exact time with you for the tour. They'll be in touch soon."
            print(f"Lead {lead_phone} completed qualification - marked as tour_ready")
        
        # Check for delay requests (AFTER tour availability check to avoid false positives)
        elif delay_detector.detect_delay_request(message):
            delay_info = delay_detector.detect_delay_request(message)
            # Pause follow-ups until the requested time
            delay_until = delay_detector.calculate_delay_until(delay_info)
            supabase_client.pause_follow_up_until(lead_phone, delay_until)
            ai_response = _generate_delay_response(delay_info)
        else:
            # Determine what fields are still missing and conversation phase
            missing_fields = supabase_client.get_missing_fields(lead)
            missing_optional = supabase_client.get_missing_optional_fields(lead)
            needs_tour_availability = supabase_client.needs_tour_availability(lead)

            print(f"[DEBUG] Missing fields analysis:")
            print(f"  missing_required_fields: {missing_fields}")
            print(f"  missing_optional_fields: {missing_optional}")
            print(f"  needs_tour_availability: {needs_tour_availability}")
            print(f"  Current lead data for missing fields check:")
            for field in REQUIRED_FIELDS + OPTIONAL_FIELDS:
                value = lead.get(field, "EMPTY")
                is_empty = not value or value.strip() == ""
                print(f"    {field}: '{value}' (empty: {is_empty})")

            # Generate AI response based on phase
            ai_response = openai_client.generate_response(
                lead, message, missing_fields, needs_tour_availability, missing_optional
            )

            # Schedule first follow-up if this is a new incomplete lead
            if (
                not lead.get("next_follow_up_time")
                and not lead.get("follow_up_paused_until")
                and missing_fields
            ):
                # Schedule first follow-up
                first_follow_up = FOLLOW_UP_SCHEDULE[0]
                supabase_client.schedule_follow_up(
                    lead_phone, first_follow_up["days"], first_follow_up["stage"]
                )
                print(
                    f"Scheduled first follow-up for {lead_phone} in {first_follow_up['days']} days"
                )

        # Send response back to the group
        # For now, we'll send to the lead's number
        # In a true group chat setup, we'd need to send to all participants
        success = telnyx_client.send_sms(lead_phone, ai_response)

        if success:
            # Update message history with AI response
            supabase_client.add_message_to_history(lead_phone, ai_response, "ai")
            print(f"AI response sent to {lead_phone}: {ai_response}")
        else:
            print(f"Failed to send AI response to {lead_phone}")

        return ai_response

    except Exception as e:
        print(f"Error processing lead message: {e}")
        # Send a fallback response
        try:
            telnyx_client = TelnyxClient()
            fallback_message = (
                "Thanks for your message. Our agent will follow up with you soon."
            )
            telnyx_client.send_sms(lead_phone, fallback_message)
            return fallback_message
        except:
            return "Error processing message"


# For local testing
if __name__ == "__main__":
    # Test event structure
    test_event = {
        "body": json.dumps(
            {
                "data": {
                    "event_type": "message.received",
                    "payload": {
                        "from": {"phone_number": "+1234567890"},
                        "to": [{"phone_number": "+1987654321"}],
                        "text": "Hi, I'm looking for a 2 bedroom apartment",
                    },
                }
            }
        )
    }

    print("Testing locally...")
    print("Loading local .env")
    load_dotenv()
    result = lambda_handler(test_event, None)
    print(f"Result: {result}")

import asyncio
import json
from typing import Dict, Any
from datetime import datetime

from services.database.lead_repository import LeadRepository
from services.messaging.telnyx_service import TelnyxService
from models.lead import Lead
from config.follow_up_config import FOLLOW_UP_SCHEDULE, FOLLOW_UP_MESSAGES, MAX_FOLLOW_UPS


# Simple service instances - created once per Lambda container
_services_initialized = False
_lead_repository = None
_messaging_service = None


def get_services():
    """Get or create service instances (singleton pattern)"""
    global _services_initialized, _lead_repository, _messaging_service
    
    if not _services_initialized:
        print("[INIT] Creating follow-up service instances")
        
        # Create services directly
        _lead_repository = LeadRepository()
        _messaging_service = TelnyxService()
        _services_initialized = True
        
        print("[INIT] Follow-up services created successfully")
    
    return _lead_repository, _messaging_service


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Follow-up handler that runs on a schedule to send follow-up messages
    """
    try:
        # Get services (created once per container)
        lead_repository, messaging_service = get_services()

        # Get leads that need follow-up
        leads_to_follow_up = asyncio.run(lead_repository.get_leads_needing_follow_up())

        print(f"Found {len(leads_to_follow_up)} leads needing follow-up")

        successful_follow_ups = 0
        failed_follow_ups = 0

        for lead in leads_to_follow_up:
            try:
                result = asyncio.run(process_follow_up(lead, lead_repository, messaging_service))
                if result:
                    successful_follow_ups += 1
                else:
                    failed_follow_ups += 1

            except Exception as e:
                print(f"Error processing follow-up for {lead.phone}: {e}")
                failed_follow_ups += 1

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Follow-up processing completed",
                "successful_follow_ups": successful_follow_ups,
                "failed_follow_ups": failed_follow_ups,
                "total_leads_processed": len(leads_to_follow_up),
            })
        }

    except Exception as e:
        print(f"Error in follow-up handler: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


async def process_follow_up(
    lead: Lead, 
    lead_repository: LeadRepository, 
    messaging_service: TelnyxService
) -> bool:
    """
    Process follow-up for a single lead
    """
    if not lead.phone:
        print("No phone number found for lead")
        return False

    current_count = lead.follow_up_count
    current_stage = lead.follow_up_stage

    print(f"Processing follow-up for {lead.phone}, count: {current_count}, stage: {current_stage}")

    # Get the appropriate follow-up message
    follow_up_message = FOLLOW_UP_MESSAGES.get(current_stage, FOLLOW_UP_MESSAGES["first"])

    # Send the follow-up message
    success = await messaging_service.send_sms(lead.phone, follow_up_message)

    if success:
        # Update message history
        await lead_repository.add_message_to_history(lead.phone, follow_up_message, "ai")

        # Increment follow-up count
        await lead_repository.update(lead.phone, {"follow_up_count": current_count + 1})

        # Schedule next follow-up if we haven't reached the maximum
        new_count = current_count + 1
        if new_count < MAX_FOLLOW_UPS:
            # Find the next follow-up in the schedule
            next_follow_up = None
            for follow_up in FOLLOW_UP_SCHEDULE:
                if follow_up["stage"] not in ["first", "second", "third", "fourth", "final"]:
                    continue

                # Map stages to count
                stage_to_count = {
                    "first": 0, "second": 1, "third": 2, "fourth": 3, "final": 4
                }

                if stage_to_count.get(follow_up["stage"]) == new_count:
                    next_follow_up = follow_up
                    break

            if next_follow_up:
                await lead_repository.schedule_follow_up(
                    lead.phone, next_follow_up["days"], next_follow_up["stage"]
                )
                print(f"Scheduled next follow-up for {lead.phone} in {next_follow_up['days']} days (stage: {next_follow_up['stage']})")
        else:
            print(f"Reached maximum follow-ups for {lead.phone}")

        return True
    else:
        print(f"Failed to send follow-up message to {lead.phone}")
        return False


# For local testing
if __name__ == "__main__":
    print("Testing follow-up handler locally...")
    result = lambda_handler({}, None)
    print(f"Result: {result}")

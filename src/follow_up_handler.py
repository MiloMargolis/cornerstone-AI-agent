import json
import os
from typing import Dict, Any, List

# Import our utility classes
from utils.supabase_client import SupabaseClient
from utils.telnyx_client import TelnyxClient
from config.follow_up_config import FOLLOW_UP_SCHEDULE, FOLLOW_UP_MESSAGES, MAX_FOLLOW_UPS

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Follow-up handler that runs on a schedule to send follow-up messages
    """
    
    try:
        # Initialize clients
        supabase_client = SupabaseClient()
        telnyx_client = TelnyxClient()
        
        # Get leads that need follow-up
        leads_to_follow_up = supabase_client.get_leads_needing_follow_up()
        
        print(f"Found {len(leads_to_follow_up)} leads needing follow-up")
        
        successful_follow_ups = 0
        failed_follow_ups = 0
        
        for lead in leads_to_follow_up:
            try:
                result = process_follow_up(lead, supabase_client, telnyx_client)
                if result:
                    successful_follow_ups += 1
                else:
                    failed_follow_ups += 1
                    
            except Exception as e:
                print(f"Error processing follow-up for {lead.get('phone', 'unknown')}: {e}")
                failed_follow_ups += 1
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Follow-up processing completed',
                'successful_follow_ups': successful_follow_ups,
                'failed_follow_ups': failed_follow_ups,
                'total_leads_processed': len(leads_to_follow_up)
            })
        }
        
    except Exception as e:
        print(f"Error in follow-up handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def process_follow_up(lead: Dict, supabase_client: SupabaseClient, telnyx_client: TelnyxClient) -> bool:
    """
    Process follow-up for a single lead
    """
    
    phone = lead.get('phone')
    if not phone:
        print("No phone number found for lead")
        return False
    
    current_count = lead.get('follow_up_count', 0)
    current_stage = lead.get('follow_up_stage', 'first')
    
    print(f"Processing follow-up for {phone}, count: {current_count}, stage: {current_stage}")
    
    # Get the appropriate follow-up message
    follow_up_message = FOLLOW_UP_MESSAGES.get(current_stage, FOLLOW_UP_MESSAGES['first'])
    
    # Send the follow-up message
    success = telnyx_client.send_sms(phone, follow_up_message)
    
    if success:
        # Update message history
        supabase_client.add_message_to_history(phone, follow_up_message, "ai")
        
        # Increment follow-up count
        supabase_client.increment_follow_up_count(phone)
        
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
                supabase_client.schedule_follow_up(phone, next_follow_up["days"], next_follow_up["stage"])
                print(f"Scheduled next follow-up for {phone} in {next_follow_up['days']} days (stage: {next_follow_up['stage']})")
        else:
            print(f"Reached maximum follow-ups for {phone}")
        
        return True
    else:
        print(f"Failed to send follow-up message to {phone}")
        return False

# For local testing
if __name__ == "__main__":
    print("Testing follow-up handler locally...")
    result = lambda_handler({}, None)
    print(f"Result: {result}") 
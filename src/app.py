import json
import os
from typing import Dict, Any

# Import our utility classes
from utils.supabase_client import SupabaseClient
from utils.openai_client import OpenAIClient
from utils.telnyx_client import TelnyxClient

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for processing Telnyx webhook events
    """
    
    # Parse the incoming webhook
    try:
        # Get the request body
        body = json.loads(event.get('body', '{}'))
        print(f"Received webhook: {json.dumps(body, indent=2)}")
        
        # Extract webhook data
        webhook_data = body.get('data', {})
        event_type = webhook_data.get('event_type')
        
        # We only care about incoming messages
        if event_type != 'message.received':
            print(f"Ignoring event type: {event_type}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Event ignored'})
            }
        
        # Extract message details
        payload = webhook_data.get('payload', {})
        from_number = payload.get('from', {}).get('phone_number')
        to_number = payload.get('to', {}).get('phone_number')
        message_text = payload.get('text')
        
        if not from_number or not message_text:
            print("Missing required message data")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required message data'})
            }
        
        # Check if this message is from the agent (ignore if so)
        agent_phone = os.getenv("AGENT_PHONE_NUMBER")
        if agent_phone and from_number == agent_phone:
            print(f"Ignoring message from agent: {from_number}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Agent message ignored'})
            }
        
        # Process the lead message
        response = process_lead_message(from_number, message_text)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message processed successfully', 'response': response})
        }
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def process_lead_message(lead_phone: str, message: str) -> str:
    """
    Process an incoming message from a lead
    """
    try:
        # Initialize clients
        supabase_client = SupabaseClient()
        openai_client = OpenAIClient()
        telnyx_client = TelnyxClient()
        
        # Get or create lead record
        lead = supabase_client.get_lead_by_phone(lead_phone)
        
        if not lead:
            # Create new lead
            print(f"Creating new lead for phone: {lead_phone}")
            lead = supabase_client.create_lead(lead_phone, message)
            if not lead:
                raise Exception("Failed to create lead record")
        
        # Extract any new information from the message
        extracted_info = openai_client.extract_lead_info(message, lead)
        
        # Check if tour availability was just provided for the first time
        tour_just_provided = (extracted_info.get("tour_availability") and 
                             (not lead.get("tour_availability") or lead.get("tour_availability").strip() == ""))
        
        # Update lead with extracted information
        if extracted_info:
            print(f"Extracted info: {extracted_info}")
            updated_lead = supabase_client.update_lead(lead_phone, extracted_info)
            if updated_lead:
                lead = updated_lead
        
        # Update message history
        supabase_client.add_message_to_history(lead_phone, message, "lead")
        
        # Check if tour availability was just provided - trigger manager response
        if tour_just_provided:
            # Set tour_ready to true
            supabase_client.set_tour_ready(lead_phone)
            ai_response = "Perfect! I have all the information I need. I'll get my manager to set up an exact time with you for the tour. They'll be in touch soon! 🏠"
        else:
            # Determine what fields are still missing and conversation phase
            missing_fields = supabase_client.get_missing_fields(lead)
            needs_tour_availability = supabase_client.needs_tour_availability(lead)
            
            # Generate AI response based on phase
            ai_response = openai_client.generate_response(lead, message, missing_fields, needs_tour_availability)
        
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
            fallback_message = "Thanks for your message! I'll have our agent follow up with you soon."
            telnyx_client.send_sms(lead_phone, fallback_message)
            return fallback_message
        except:
            return "Error processing message"

# For local testing
if __name__ == "__main__":
    # Test event structure
    test_event = {
        'body': json.dumps({
            'data': {
                'event_type': 'message.received',
                'payload': {
                    'from': {
                        'phone_number': '+1234567890'
                    },
                    'to': {
                        'phone_number': '+1987654321'
                    },
                    'text': 'Hi, I\'m looking for a 2 bedroom apartment'
                }
            }
        })
    }
    
    print("Testing locally...")
    result = lambda_handler(test_event, None)
    print(f"Result: {result}") 
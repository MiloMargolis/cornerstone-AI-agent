import os

from services.database.lead_repository import LeadRepository
from services.messaging.telnyx_service import TelnyxService
from services.ai.openai_service import OpenAIService
from services.delay_detection.delay_detection_service import DelayDetectionService
from models.lead import Lead
from config.follow_up_config import FOLLOW_UP_SCHEDULE


class LeadProcessor:
    """Core business logic for processing lead messages"""

    def __init__(
        self,
        lead_repository: LeadRepository,
        messaging_service: TelnyxService,
        ai_service: OpenAIService,
        delay_detection_service: DelayDetectionService,
    ):
        self.lead_repository = lead_repository
        self.messaging_service = messaging_service
        self.ai_service = ai_service
        self.delay_detection_service = delay_detection_service
        self.agent_phone = os.getenv("AGENT_PHONE_NUMBER")

    def _create_virtual_lead(self, lead: Lead, extracted_info: dict) -> Lead:
        """Create a virtual lead state that includes newly extracted information"""
        # Create a copy of the lead with extracted info applied
        virtual_data = lead.to_dict()
        
        # Apply extracted info to virtual data
        for field, value in extracted_info.items():
            if value and str(value).strip():
                virtual_data[field] = value
        
        # Create new Lead instance from virtual data
        return Lead.from_dict(virtual_data)

    async def process_lead_message(self, lead_phone: str, message: str) -> str:
        """Process an incoming message from a lead"""
        try:
            # Get or create lead record
            lead = await self.lead_repository.get_by_phone(lead_phone)

            if not lead:
                # Create new lead
                print(f"Creating new lead for phone: {lead_phone}")
                lead = Lead(phone=lead_phone)
                lead = await self.lead_repository.create(lead)
                if not lead:
                    raise Exception("Failed to create lead record")

            # Extract any new information from the message
            extracted_info = await self.ai_service.extract_lead_info(message, lead)

            # Create virtual lead state that includes extracted info
            if extracted_info:
                print(f"[DEBUG] Extracted info: {extracted_info}")
                # Create virtual lead with extracted info applied
                virtual_lead = self._create_virtual_lead(lead, extracted_info)
                
                # Update database with extracted information
                updated_lead = await self.lead_repository.update(
                    lead_phone, extracted_info
                )
                if updated_lead:
                    lead = updated_lead
                    # Use virtual lead for all subsequent operations to ensure context accuracy
                    lead = virtual_lead
                    field_values = {
                        field: getattr(lead, field, "EMPTY")
                        for field in [
                            "move_in_date",
                            "price",
                            "beds",
                            "baths",
                            "location",
                            "amenities",
                            "tour_availability",
                            "tour_ready",
                        ]
                    }
                    print(
                        f"[DEBUG] Lead updated successfully. Current lead data: {field_values}"
                    )
                else:
                    print(
                        f"[ERROR] Failed to update lead with extracted info: {extracted_info}"
                    )
            else:
                print(f"[DEBUG] No information extracted from message: '{message}'")

            # Update message history BEFORE AI response generation to ensure context accuracy
            await self.lead_repository.add_message_to_history(
                lead_phone, message, "lead"
            )

            # Check for delay requests
            message_context = {}
            delay_info = await self.delay_detection_service.detect_delay_request(message)
            if delay_info:
                # Pause follow-ups until the requested time
                delay_until = await self.delay_detection_service.calculate_delay_until(delay_info)
                await self.lead_repository.pause_follow_up_until(lead_phone, delay_until)
                message_context = {
                    "delay_detected": True,
                    "delay_duration": delay_info.get("delay_days", "later"),
                    "delay_type": delay_info.get("delay_type", "general")
                }

            # Check if conversation is already complete (tour_ready = True)
            if lead.tour_ready:
                # Conversation is complete - stay completely silent
                print(
                    f"Lead {lead_phone} is tour_ready - staying silent (no response sent)"
                )
                return "SILENT_TOUR_READY"  # Return early, no SMS sent

            # Check if tour availability was just provided - trigger manager response
            if (
                extracted_info
                and extracted_info.get("tour_availability")
                and not lead.tour_availability
            ):
                # Set tour_ready to true
                print(
                    f"Lead {lead_phone} provided tour availability - marking as tour_ready"
                )
                await self.lead_repository.set_tour_ready(lead_phone)

                # Send notification to agent
                await self._send_agent_notification(lead_phone, lead)

                ai_response = (
                    "Perfect! I have all the information I need. "
                    "I'll get my teammate to set up an exact time with you for the tour. "
                    "They'll be in touch soon."
                )
                print(
                    f"Lead {lead_phone} completed qualification - marked as tour_ready"
                )

            elif (
                not lead.tour_ready
                and not (extracted_info and extracted_info.get("tour_availability") and not lead.tour_availability)
            ):
                # Determine what fields are still missing and conversation phase
                # Use the virtual lead state for accurate missing field calculation
                missing_fields = await self.lead_repository.get_missing_fields(lead)
                missing_optional = (
                    await self.lead_repository.get_missing_optional_fields(lead)
                )
                needs_tour_availability = (
                    await self.lead_repository.needs_tour_availability(lead)
                )
                missing_fields_analysis = {
                    "missing_required_fields": missing_fields,
                    "missing_optional_fields": missing_optional,
                    "needs_tour_availability": needs_tour_availability,
                }
                print(f"[DEBUG] Missing fields analysis: {missing_fields_analysis}")

                # Generate AI response using conversation controller
                ai_response, should_mark_tour_ready = await self.ai_service.generate_response(
                    lead,  # Now includes extracted info via virtual lead
                    message,
                    missing_fields,
                    needs_tour_availability,
                    missing_optional,
                    extracted_info,
                    message_context,
                )

                # Check if conversation controller determined lead is ready for agent handoff
                if should_mark_tour_ready:
                    # Set tour_ready to true
                    print(f"[DEBUG] Lead {lead_phone} ready for agent handoff - marking as tour_ready")
                    await self.lead_repository.set_tour_ready(lead_phone)
                    
                    # Send notification to agent IMMEDIATELY (before sending response to user)
                    print(f"[DEBUG] Sending agent notification IMMEDIATELY for {lead_phone}")
                    await self._send_agent_notification(lead_phone, lead)
                    print(f"[DEBUG] Agent notification sent for {lead_phone}")

                # Schedule first follow-up if this is a new incomplete lead
                if (
                    not lead.next_follow_up_time
                    and not lead.follow_up_paused_until
                    and missing_fields
                ):
                    # Schedule first follow-up
                    first_follow_up = FOLLOW_UP_SCHEDULE[0]
                    await self.lead_repository.schedule_follow_up(
                        lead_phone, first_follow_up["days"], first_follow_up["stage"]
                    )
                    print(
                        f"Scheduled first follow-up for {lead_phone} in {first_follow_up['days']} days"
                    )

            # Send response back to the lead
            print(f"[DEBUG] Sending AI response to user {lead_phone}: {ai_response}")
            success = await self.messaging_service.send_sms(lead_phone, ai_response)

            if success:
                # Update message history with AI response
                await self.lead_repository.add_message_to_history(
                    lead_phone, ai_response, "ai"
                )
                print(f"AI response sent to {lead_phone}: {ai_response}")
            else:
                print(f"Failed to send AI response to {lead_phone}")

            return ai_response

        except Exception as e:
            print(f"Error processing lead message: {e}")
            # Send a fallback response
            try:
                fallback_message = (
                    "Thanks for your message. Our agent will follow up with you soon."
                )
                await self.messaging_service.send_sms(lead_phone, fallback_message)
                return fallback_message
            except:
                return "Error processing message"

    async def _send_agent_notification(self, lead_phone: str, lead: Lead):
        """Send notification to agent that lead is ready for tour"""
        if self.agent_phone:
            lead_name = lead.name or "Lead"
            agent_message = f"{lead_name} with phone number {lead_phone} is ready for a tour"

            agent_sms_success = (
                await self.messaging_service.send_agent_notification(
                    self.agent_phone, agent_message
                )
            )
            if agent_sms_success:
                print(
                    f"Agent notification sent to {self.agent_phone}: {agent_message}"
                )
            else:
                print(
                    f"Failed to send agent notification to {self.agent_phone}"
                )
        else:
            print(
                "No AGENT_PHONE_NUMBER configured - skipping agent notification"
            )



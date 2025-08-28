import os

from services.interfaces import (
    ILeadRepository,
    IMessagingService,
    IAIService,
    IDelayDetectionService,
)
from models.lead import Lead
from config.follow_up_config import FOLLOW_UP_SCHEDULE


class LeadProcessor:
    """Core business logic for processing lead messages"""

    def __init__(
        self,
        lead_repository: ILeadRepository,
        messaging_service: IMessagingService,
        ai_service: IAIService,
        delay_detection_service: IDelayDetectionService,
    ):
        self.lead_repository = lead_repository
        self.messaging_service = messaging_service
        self.ai_service = ai_service
        self.delay_detection_service = delay_detection_service
        self.agent_phone = os.getenv("AGENT_PHONE_NUMBER")

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

            # Update lead with extracted information
            if extracted_info:
                print(f"[DEBUG] Extracted info: {extracted_info}")
                updated_lead = await self.lead_repository.update(
                    lead_phone, extracted_info
                )
                if updated_lead:
                    lead = updated_lead
                    # Refresh lead from database to ensure we have the most current data
                    refreshed_lead = await self.lead_repository.get_by_phone(lead_phone)
                    if refreshed_lead:
                        lead = refreshed_lead
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

            # Update message history
            await self.lead_repository.add_message_to_history(
                lead_phone, message, "lead"
            )

            # Check for delay requests
            delay_info = await self.delay_detection_service.detect_delay_request(
                message
            )
            if delay_info:
                # Pause follow-ups until the requested time
                delay_until = await self.delay_detection_service.calculate_delay_until(
                    delay_info
                )
                await self.lead_repository.pause_follow_up_until(
                    lead_phone, delay_until
                )
                ai_response = await self.ai_service.generate_delay_response(delay_info)

            # Check if conversation is already complete (tour_ready = True)
            elif lead.tour_ready:
                # Conversation is complete - stay completely silent
                print(
                    f"Lead {lead_phone} is tour_ready - staying silent (no response sent)"
                )
                return "SILENT_TOUR_READY"  # Return early, no SMS sent

            # Check if tour availability was just provided - trigger manager response
            elif (
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

                ai_response = (
                    "Perfect! I have all the information I need. "
                    "I'll get my teammate to set up an exact time with you for the tour. "
                    "They'll be in touch soon."
                )
                print(
                    f"Lead {lead_phone} completed qualification - marked as tour_ready"
                )

            else:
                # Determine what fields are still missing and conversation phase
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

                # Generate AI response based on phase
                ai_response = await self.ai_service.generate_response(
                    lead,
                    message,
                    missing_fields,
                    needs_tour_availability,
                    missing_optional,
                    extracted_info,
                )

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

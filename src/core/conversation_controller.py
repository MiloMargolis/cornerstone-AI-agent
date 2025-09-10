from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from models.lead import Lead
from utils.constants import REQUIRED_FIELDS, OPTIONAL_FIELDS


class ConversationAction(Enum):
    """Enumeration of possible conversation actions"""
    INITIAL_OUTREACH = "initial_outreach"
    CONTINUE_QUALIFICATION = "continue_qualification"
    SUMMARY_CONFIRMATION = "summary_confirmation"
    TRANSITION_TO_OPTIONAL = "transition_to_optional"
    CLARIFY_INFORMATION = "clarify_information"
    ACKNOWLEDGE_DELAY = "acknowledge_delay"
    GENTLE_REDIRECT = "gentle_redirect"
    REQUEST_AVAILABILITY = "request_availability"
    READY_FOR_AGENT = "ready_for_agent"
    FOLLOW_UP_CHECK_IN = "follow_up_check_in"


@dataclass
class ConversationContext:
    """Context data for conversation actions"""
    action: ConversationAction
    prompt_template: str
    context_data: Dict[str, Any]
    extracted_info: Optional[Dict[str, Any]] = None
    message_context: Optional[Dict[str, Any]] = None
    should_mark_tour_ready: bool = False


@dataclass
class ExtractionAnalysis:
    """Analysis of information extraction results"""
    has_new_data: bool
    is_unclear: bool
    unclear_fields: List[str]
    newly_extracted: Dict[str, Any]
    extraction_confidence: float


class ConversationController:
    """Manages conversation flow and decision making"""
    
    def __init__(self):
        self.prompt_templates = {
            ConversationAction.INITIAL_OUTREACH: "initial_qualification.tmpl",
            ConversationAction.CONTINUE_QUALIFICATION: "follow_up_required.tmpl",
            ConversationAction.SUMMARY_CONFIRMATION: "summary_confirmation.tmpl",
            ConversationAction.TRANSITION_TO_OPTIONAL: "optional_questions.tmpl",
            ConversationAction.CLARIFY_INFORMATION: "clarification_request.tmpl",
            ConversationAction.ACKNOWLEDGE_DELAY: "delay_acknowledgment.tmpl",
            ConversationAction.GENTLE_REDIRECT: "gentle_redirect.tmpl",
            ConversationAction.REQUEST_AVAILABILITY: "tour_scheduling.tmpl",
            ConversationAction.READY_FOR_AGENT: "agent_handoff.tmpl",
            ConversationAction.FOLLOW_UP_CHECK_IN: "follow_up_checkin.tmpl",
        }

    def determine_conversation_action(
        self, 
        lead: Lead, 
        extracted_info: Dict[str, Any], 
        message: str,
        message_context: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        print(f"[DEBUG] Determining conversation action for lead {lead.phone}")
        print(f"[DEBUG] Lead is_qualified: {lead.is_qualified}")
        print(f"[DEBUG] Has been summarized: {self._has_been_summarized(lead)}")
        print(f"[DEBUG] Has completed optional: {self._has_completed_optional_questions(lead)}")
        print(f"[DEBUG] Extraction has new data: {bool(extracted_info)}")
        print(f"[DEBUG] Missing required fields: {lead.missing_required_fields}")
        print(f"[DEBUG] Missing optional fields: {lead.missing_optional_fields}")
        """
        Determine the appropriate conversation action based on lead state and message content
        """
        # Step 1: Classify interaction type
        if self._is_new_lead(lead):
            return self._build_initial_outreach_context(lead, message)
        
        # Step 2: Check for delay requests first
        if message_context and message_context.get("delay_detected"):
            return self._build_delay_context(message_context)
        
        # Step 3: Analyze extraction quality
        extraction_analysis = self._analyze_extraction(extracted_info, lead)
        
        if extraction_analysis.has_new_data:
            if lead.is_qualified:
                # Check if this is the first time they've completed required fields
                if not self._has_been_summarized(lead):
                    return self._build_summary_confirmation_context(lead, extraction_analysis)
                elif not self._has_completed_optional_questions(lead):
                    return self._build_optional_context(lead, extraction_analysis)
                else:
                    return self._build_handoff_context(lead)
            else:
                return self._build_continuation_context(lead, extraction_analysis)
        
        elif extraction_analysis.is_unclear:
            return self._build_clarification_context(extraction_analysis)
        
        # Handle qualified leads when no new extraction
        elif lead.is_qualified:
            # Lead is qualified - check conversation phase
            if not self._has_been_summarized(lead):
                return self._build_summary_confirmation_context(lead, extraction_analysis)
            elif not self._has_completed_optional_questions(lead):
                return self._build_optional_context(lead, extraction_analysis)
            else:
                return self._build_handoff_context(lead)
        
        # Step 5: Default to gentle redirect
        else:
            return self._build_redirect_context(lead)

    def _is_new_lead(self, lead: Lead) -> bool:
        """Check if this is a new lead with no conversation history"""
        return (
            not lead.chat_history or 
            not lead.chat_history.strip()
        )

    def _has_optional_gaps(self, lead: Lead) -> bool:
        """Check if lead has gaps in optional fields"""
        return bool(lead.missing_optional_fields)
    
    def _has_been_summarized(self, lead: Lead) -> bool:
        """Check if lead has already been summarized (completed required fields)"""
        # This is a simple heuristic - in a real implementation, you might track this in the database
        # For now, we'll check if they have optional fields filled or tour availability
        # Also check if they've confirmed the summary (indicated by recent confirmation messages)
        return bool(lead.boston_rental_experience or lead.tour_availability or self._has_confirmed_summary(lead))
    
    def _has_completed_optional_questions(self, lead: Lead) -> bool:
        """Check if lead has completed optional questions phase"""
        # Check if they have the optional field filled OR if they've been told they're ready for agent
        return bool(lead.boston_rental_experience or self._has_been_told_ready_for_agent(lead))
    
    def _has_been_told_ready_for_agent(self, lead: Lead) -> bool:
        """Check if lead has been told they're ready for agent handoff"""
        if not lead.chat_history:
            return False
        
        # Look for messages indicating they're ready for agent
        agent_ready_phrases = [
            "ready to send your information to my human agent",
            "send your information to my human agent",
            "human agent who will help you",
            "agent who will help you schedule"
        ]
        
        recent_messages = lead.chat_history.split("\n")[-5:]  # Last 5 messages
        for message in recent_messages:
            message_lower = message.lower()
            if any(phrase in message_lower for phrase in agent_ready_phrases):
                return True
        
        return False
    
    def _has_confirmed_summary(self, lead: Lead) -> bool:
        """Check if lead has confirmed the summary"""
        if not lead.chat_history:
            return False
        
        # Look for confirmation messages in recent chat history
        confirmation_phrases = [
            "looks good", "yes", "correct", "move on", "ready", "sounds good", 
            "perfect", "that's right", "confirmed", "okay", "good"
        ]
        
        recent_messages = lead.chat_history.split("\n")[-5:]  # Last 5 messages
        for message in recent_messages:
            message_lower = message.lower()
            if any(phrase in message_lower for phrase in confirmation_phrases):
                return True
        
        return False

    def _analyze_extraction(self, extracted_info: Dict[str, Any], lead: Lead) -> ExtractionAnalysis:
        """Analyze the quality and content of extracted information"""
        if not extracted_info:
            return ExtractionAnalysis(
                has_new_data=False,
                is_unclear=False,
                unclear_fields=[],
                newly_extracted={},
                extraction_confidence=0.0
            )
        
        # Check for new data
        newly_extracted = {}
        for field, value in extracted_info.items():
            if value and str(value).strip():
                current_value = getattr(lead, field, None)
                if not current_value or str(current_value).strip() != str(value).strip():
                    newly_extracted[field] = value
        
        has_new_data = bool(newly_extracted)
        
        # Check for unclear extractions (low confidence or partial data)
        unclear_fields = []
        extraction_confidence = 1.0
        
        # Simple heuristic: if extraction has very short values or unclear patterns
        for field, value in extracted_info.items():
            if value and str(value).strip():
                value_str = str(value).strip()
                if len(value_str) < 2 or value_str.lower() in ['yes', 'no', 'maybe', 'idk', 'idk']:
                    unclear_fields.append(field)
                    extraction_confidence *= 0.7
        
        is_unclear = bool(unclear_fields) or extraction_confidence < 0.8
        
        return ExtractionAnalysis(
            has_new_data=has_new_data,
            is_unclear=is_unclear,
            unclear_fields=unclear_fields,
            newly_extracted=newly_extracted,
            extraction_confidence=extraction_confidence
        )

    def _build_initial_outreach_context(self, lead: Lead, message: str) -> ConversationContext:
        """Build context for initial outreach to new leads"""
        return ConversationContext(
            action=ConversationAction.INITIAL_OUTREACH,
            prompt_template=self.prompt_templates[ConversationAction.INITIAL_OUTREACH],
            context_data={
                "greeting": "Welcome! I'm here to help you find your perfect apartment.",
                "basic_questions": "Let me ask a few quick questions to understand what you're looking for.",
                "lead_name": lead.name or "there",
                "conversation_start": True
            }
        )

    def _build_continuation_context(self, lead: Lead, extraction_analysis: ExtractionAnalysis) -> ConversationContext:
        """Build context for continuing qualification with existing leads"""
        return ConversationContext(
            action=ConversationAction.CONTINUE_QUALIFICATION,
            prompt_template=self.prompt_templates[ConversationAction.CONTINUE_QUALIFICATION],
            context_data={
                "what_we_have": self._format_known_info(lead),
                "what_we_need": self._format_missing_fields(lead.missing_required_fields),
                "logical_next": self._get_logical_next_questions(lead),
                "newly_extracted": extraction_analysis.newly_extracted,
                "progress_acknowledgment": self._acknowledge_progress(extraction_analysis)
            },
            extracted_info=extraction_analysis.newly_extracted
        )

    def _build_summary_confirmation_context(self, lead: Lead, extraction_analysis: ExtractionAnalysis) -> ConversationContext:
        """Build context for summarizing and confirming required information"""
        return ConversationContext(
            action=ConversationAction.SUMMARY_CONFIRMATION,
            prompt_template=self.prompt_templates[ConversationAction.SUMMARY_CONFIRMATION],
            context_data={
                "qualification_summary": self._format_qualification_summary(lead),
                "progress_acknowledgment": self._acknowledge_progress(extraction_analysis),
                "confirmation_request": "Does this look correct, or would you like to change anything?"
            },
            extracted_info=extraction_analysis.newly_extracted
        )

    def _build_optional_context(self, lead: Lead, extraction_analysis: ExtractionAnalysis) -> ConversationContext:
        """Build context for transitioning to optional questions"""
        return ConversationContext(
            action=ConversationAction.TRANSITION_TO_OPTIONAL,
            prompt_template=self.prompt_templates[ConversationAction.TRANSITION_TO_OPTIONAL],
            context_data={
                "progress_acknowledgment": self._acknowledge_progress(extraction_analysis),
                "optional_fields": lead.missing_optional_fields,
                "qualification_complete": True,
                "next_phase": "optional_questions"
            },
            extracted_info=extraction_analysis.newly_extracted
        )

    def _build_clarification_context(self, extraction_analysis: ExtractionAnalysis) -> ConversationContext:
        """Build context for clarifying unclear information"""
        return ConversationContext(
            action=ConversationAction.CLARIFY_INFORMATION,
            prompt_template=self.prompt_templates[ConversationAction.CLARIFY_INFORMATION],
            context_data={
                "unclear_field": extraction_analysis.unclear_fields[0] if extraction_analysis.unclear_fields else "information",
                "request_specifics": self._get_clarification_request(extraction_analysis.unclear_fields),
                "extraction_confidence": extraction_analysis.extraction_confidence
            }
        )

    def _build_delay_context(self, message_context: Dict[str, Any]) -> ConversationContext:
        """Build context for acknowledging delay requests"""
        return ConversationContext(
            action=ConversationAction.ACKNOWLEDGE_DELAY,
            prompt_template=self.prompt_templates[ConversationAction.ACKNOWLEDGE_DELAY],
            context_data={
                "delay_duration": message_context.get("delay_duration", "later"),
                "reassurance": "Feel free to message me anytime if you have questions before then.",
                "delay_type": message_context.get("delay_type", "general")
            },
            message_context=message_context
        )

    def _build_redirect_context(self, lead: Lead) -> ConversationContext:
        """Build context for gently redirecting conversation back to qualification"""
        return ConversationContext(
            action=ConversationAction.GENTLE_REDIRECT,
            prompt_template=self.prompt_templates[ConversationAction.GENTLE_REDIRECT],
            context_data={
                "conversation_purpose": "I'm here to help you find the perfect apartment.",
                "next_needed": self._format_missing_fields(lead.missing_required_fields),
                "what_we_have": self._format_known_info(lead)
            }
        )

    def _build_tour_context(self, lead: Lead, extraction_analysis: Optional[ExtractionAnalysis] = None) -> ConversationContext:
        """Build context for requesting tour availability"""
        return ConversationContext(
            action=ConversationAction.REQUEST_AVAILABILITY,
            prompt_template=self.prompt_templates[ConversationAction.REQUEST_AVAILABILITY],
            context_data={
                "qualification_summary": self._format_qualification_summary(lead),
                "availability_request": "When are you available for property tours?",
                "progress_acknowledgment": self._acknowledge_progress(extraction_analysis) if extraction_analysis else None
            },
            extracted_info=extraction_analysis.newly_extracted if extraction_analysis else None
        )

    def _build_handoff_context(self, lead: Lead) -> ConversationContext:
        """Build context for agent handoff"""
        print(f"[DEBUG] Building handoff context for lead {lead.phone} - setting should_mark_tour_ready=True")
        
        return ConversationContext(
            action=ConversationAction.READY_FOR_AGENT,
            prompt_template=None,  # No prompt template needed - direct response
            context_data={
                "direct_response": "Perfect! I'm sending your information to my human agent who will help you schedule tours. They'll be in touch soon!"
            },
            should_mark_tour_ready=True
        )

    # Helper methods for context building
    def _format_known_info(self, lead: Lead) -> str:
        """Format what we know about the lead"""
        known_fields = []
        for field in REQUIRED_FIELDS + OPTIONAL_FIELDS:
            value = getattr(lead, field, None)
            if value and str(value).strip():
                known_fields.append(f"{field}: {value}")
        return ", ".join(known_fields) if known_fields else "No information yet"

    def _format_missing_fields(self, missing_fields: List[str]) -> str:
        """Format missing fields in a user-friendly way"""
        if not missing_fields:
            return "All required information collected"
        
        field_mappings = {
            "move_in_date": "move-in date",
            "price": "budget",
            "beds": "bedrooms",
            "baths": "bathrooms",
            "location": "preferred area",
            "amenities": "amenities",
            "boston_rental_experience": "rental experience"
        }
        
        formatted_fields = [field_mappings.get(field, field) for field in missing_fields]
        return ", ".join(formatted_fields)

    def _get_logical_next_questions(self, lead: Lead) -> List[str]:
        """Get logical next questions based on what's missing"""
        missing = lead.missing_required_fields
        
        # Group related questions
        if "beds" in missing and "baths" in missing:
            return ["bedrooms and bathrooms"]
        elif "price" in missing and "location" in missing:
            return ["budget and preferred area"]
        elif "move_in_date" in missing and "amenities" in missing:
            return ["move-in date and amenities"]
        else:
            return missing[:2]  # Take first 2 missing fields

    def _acknowledge_progress(self, extraction_analysis: ExtractionAnalysis) -> str:
        """Acknowledge newly extracted information"""
        if not extraction_analysis.newly_extracted:
            return ""
        
        field_mappings = {
            "move_in_date": "move-in date",
            "price": "budget",
            "beds": "bedrooms",
            "baths": "bathrooms",
            "location": "area",
            "amenities": "amenities"
        }
        
        acknowledged = []
        for field, value in extraction_analysis.newly_extracted.items():
            field_name = field_mappings.get(field, field)
            acknowledged.append(f"{field_name}: {value}")
        
        return f"Got it - {', '.join(acknowledged)}."

    def _get_clarification_request(self, unclear_fields: List[str]) -> str:
        """Generate clarification request for unclear fields"""
        if not unclear_fields:
            return "Could you provide more details?"
        
        field_mappings = {
            "move_in_date": "move-in date",
            "price": "budget",
            "beds": "number of bedrooms",
            "baths": "number of bathrooms",
            "location": "preferred area",
            "amenities": "amenities"
        }
        
        field_name = field_mappings.get(unclear_fields[0], unclear_fields[0])
        return f"Could you clarify your {field_name}?"

    def _format_qualification_summary(self, lead: Lead) -> str:
        """Format a summary of the lead's qualification"""
        summary_parts = []
        
        if lead.beds and lead.baths:
            summary_parts.append(f"{lead.beds} bed, {lead.baths} bath")
        
        if lead.price:
            summary_parts.append(f"budget: {lead.price}")
        
        if lead.location:
            summary_parts.append(f"area: {lead.location}")
        
        if lead.move_in_date:
            summary_parts.append(f"move-in: {lead.move_in_date}")
        
        return ", ".join(summary_parts) if summary_parts else "Qualified lead"

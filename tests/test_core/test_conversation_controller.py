import pytest
from datetime import datetime
from core.conversation_controller import (
    ConversationController, 
    ConversationAction, 
    ConversationContext,
    ExtractionAnalysis
)
from models.lead import Lead


class TestConversationController:
    """Test cases for ConversationController"""

    def setup_method(self):
        """Set up test fixtures"""
        self.controller = ConversationController()

    def test_new_lead_detection(self):
        """Test detection of new leads"""
        # New lead with no history
        new_lead = Lead(phone="+1234567890")
        assert self.controller._is_new_lead(new_lead) is True

        # Lead with chat history
        existing_lead = Lead(phone="+1234567890", chat_history="Some conversation")
        assert self.controller._is_new_lead(existing_lead) is False

        # Lead with follow-up count
        follow_up_lead = Lead(phone="+1234567890", follow_up_count=1)
        assert self.controller._is_new_lead(follow_up_lead) is False

    def test_extraction_analysis_new_data(self):
        """Test extraction analysis with new data"""
        lead = Lead(phone="+1234567890", beds="2", baths="1")
        extracted_info = {"price": "2000", "location": "Boston"}
        
        analysis = self.controller._analyze_extraction(extracted_info, lead)
        
        assert analysis.has_new_data is True
        assert analysis.is_unclear is False
        assert analysis.newly_extracted == {"price": "2000", "location": "Boston"}
        assert analysis.extraction_confidence == 1.0

    def test_extraction_analysis_unclear_data(self):
        """Test extraction analysis with unclear data"""
        lead = Lead(phone="+1234567890")
        extracted_info = {"price": "yes", "location": "idk"}
        
        analysis = self.controller._analyze_extraction(extracted_info, lead)
        
        assert analysis.has_new_data is True
        assert analysis.is_unclear is True
        assert "price" in analysis.unclear_fields
        assert "location" in analysis.unclear_fields
        assert analysis.extraction_confidence < 1.0

    def test_extraction_analysis_no_data(self):
        """Test extraction analysis with no data"""
        lead = Lead(phone="+1234567890")
        extracted_info = {}
        
        analysis = self.controller._analyze_extraction(extracted_info, lead)
        
        assert analysis.has_new_data is False
        assert analysis.is_unclear is False
        assert analysis.newly_extracted == {}
        assert analysis.extraction_confidence == 0.0

    def test_initial_outreach_context(self):
        """Test building initial outreach context"""
        lead = Lead(phone="+1234567890", name="John")
        message = "Hi"
        
        context = self.controller._build_initial_outreach_context(lead, message)
        
        assert context.action == ConversationAction.INITIAL_OUTREACH
        assert context.prompt_template == "initial_qualification.tmpl"
        assert context.context_data["lead_name"] == "John"
        assert context.context_data["conversation_start"] is True

    def test_continuation_context(self):
        """Test building continuation context"""
        lead = Lead(phone="+1234567890", beds="2", baths="1")
        analysis = ExtractionAnalysis(
            has_new_data=True,
            is_unclear=False,
            unclear_fields=[],
            newly_extracted={"price": "2000"},
            extraction_confidence=1.0
        )
        
        context = self.controller._build_continuation_context(lead, analysis)
        
        assert context.action == ConversationAction.CONTINUE_QUALIFICATION
        assert context.prompt_template == "follow_up_required.tmpl"
        assert "what_we_have" in context.context_data
        assert "what_we_need" in context.context_data
        assert context.extracted_info == {"price": "2000"}

    def test_summary_confirmation_context(self):
        """Test building summary confirmation context"""
        lead = Lead(phone="+1234567890")
        # Mock qualified lead
        lead.beds = "2"
        lead.baths = "1"
        lead.price = "2000"
        lead.location = "Boston"
        lead.move_in_date = "July 1"
        lead.amenities = "Parking"
        
        analysis = ExtractionAnalysis(
            has_new_data=True,
            is_unclear=False,
            unclear_fields=[],
            newly_extracted={"amenities": "Parking"},
            extraction_confidence=1.0
        )
        
        context = self.controller._build_summary_confirmation_context(lead, analysis)
        
        assert context.action == ConversationAction.SUMMARY_CONFIRMATION
        assert context.prompt_template == "summary_confirmation.tmpl"
        assert "qualification_summary" in context.context_data
        assert "confirmation_request" in context.context_data

    def test_optional_context(self):
        """Test building optional context"""
        lead = Lead(phone="+1234567890")
        # Mock lead to be qualified with optional fields
        lead.beds = "2"
        lead.baths = "1"
        lead.price = "2000"
        lead.location = "Boston"
        lead.move_in_date = "July 1"
        lead.amenities = "Parking"
        lead.boston_rental_experience = "Yes"  # Already summarized
        
        analysis = ExtractionAnalysis(
            has_new_data=True,
            is_unclear=False,
            unclear_fields=[],
            newly_extracted={"amenities": "Parking"},
            extraction_confidence=1.0
        )
        
        context = self.controller._build_optional_context(lead, analysis)
        
        assert context.action == ConversationAction.TRANSITION_TO_OPTIONAL
        assert context.prompt_template == "optional_questions.tmpl"
        assert context.context_data["qualification_complete"] is True

    def test_clarification_context(self):
        """Test building clarification context"""
        analysis = ExtractionAnalysis(
            has_new_data=True,
            is_unclear=True,
            unclear_fields=["price"],
            newly_extracted={"price": "yes"},
            extraction_confidence=0.7
        )
        
        context = self.controller._build_clarification_context(analysis)
        
        assert context.action == ConversationAction.CLARIFY_INFORMATION
        assert context.prompt_template == "clarification_request.tmpl"
        assert context.context_data["unclear_field"] == "price"

    def test_delay_context(self):
        """Test building delay context"""
        message_context = {
            "delay_detected": True,
            "delay_duration": "tomorrow",
            "delay_type": "general"
        }
        
        context = self.controller._build_delay_context(message_context)
        
        assert context.action == ConversationAction.ACKNOWLEDGE_DELAY
        assert context.prompt_template == "delay_acknowledgment.tmpl"
        assert context.context_data["delay_duration"] == "tomorrow"

    def test_redirect_context(self):
        """Test building redirect context"""
        lead = Lead(phone="+1234567890", beds="2")
        
        context = self.controller._build_redirect_context(lead)
        
        assert context.action == ConversationAction.GENTLE_REDIRECT
        assert context.prompt_template == "gentle_redirect.tmpl"
        assert "conversation_purpose" in context.context_data

    def test_tour_context(self):
        """Test building tour context"""
        lead = Lead(phone="+1234567890")
        # Mock qualified lead
        lead.beds = "2"
        lead.baths = "1"
        lead.price = "2000"
        lead.location = "Boston"
        lead.move_in_date = "July 1"
        lead.amenities = "Parking"
        
        context = self.controller._build_tour_context(lead)
        
        assert context.action == ConversationAction.REQUEST_AVAILABILITY
        assert context.prompt_template == "tour_scheduling.tmpl"
        assert "qualification_summary" in context.context_data

    def test_handoff_context(self):
        """Test building handoff context"""
        lead = Lead(phone="+1234567890", tour_availability="Weekends")
        # Mock qualified lead
        lead.beds = "2"
        lead.baths = "1"
        lead.price = "2000"
        lead.location = "Boston"
        lead.move_in_date = "July 1"
        lead.amenities = "Parking"
        
        context = self.controller._build_handoff_context(lead)
        
        assert context.action == ConversationAction.READY_FOR_AGENT
        assert context.prompt_template is None  # No prompt template needed for direct response
        assert "direct_response" in context.context_data
        assert context.context_data["direct_response"] == "Perfect! I'm ready to send your information to my human agent who will help you schedule tours. They'll be in touch soon!"
        assert context.should_mark_tour_ready is True

    def test_determine_conversation_action_new_lead(self):
        """Test conversation action determination for new leads"""
        lead = Lead(phone="+1234567890")
        extracted_info = {}
        message = "Hi"
        
        context = self.controller.determine_conversation_action(lead, extracted_info, message)
        
        assert context.action == ConversationAction.INITIAL_OUTREACH

    def test_determine_conversation_action_delay_request(self):
        """Test conversation action determination for delay requests"""
        lead = Lead(phone="+1234567890", chat_history="Previous conversation")
        extracted_info = {}
        message = "Can you follow up later?"
        message_context = {"delay_detected": True, "delay_duration": "tomorrow"}
        
        context = self.controller.determine_conversation_action(
            lead, extracted_info, message, message_context
        )
        
        assert context.action == ConversationAction.ACKNOWLEDGE_DELAY

    def test_determine_conversation_action_clear_extraction(self):
        """Test conversation action determination for clear extraction"""
        lead = Lead(phone="+1234567890", chat_history="Previous conversation")
        extracted_info = {"price": "2000", "location": "Boston"}
        message = "My budget is 2000 and I want to live in Boston"
        
        context = self.controller.determine_conversation_action(lead, extracted_info, message)
        
        assert context.action == ConversationAction.CONTINUE_QUALIFICATION

    def test_determine_conversation_action_unclear_extraction(self):
        """Test conversation action determination for unclear extraction"""
        lead = Lead(phone="+1234567890", chat_history="Previous conversation")
        extracted_info = {"price": "yes"}
        message = "Yes"
        
        context = self.controller.determine_conversation_action(lead, extracted_info, message)
        
        assert context.action == ConversationAction.CLARIFY_INFORMATION

    def test_determine_conversation_action_qualified_lead(self):
        """Test conversation action determination for qualified leads"""
        lead = Lead(phone="+1234567890", chat_history="Previous conversation")
        # Mock qualified lead
        lead.beds = "2"
        lead.baths = "1"
        lead.price = "2000"
        lead.location = "Boston"
        lead.move_in_date = "July 1"
        lead.amenities = "Parking"
        
        extracted_info = {}
        message = "What's next?"
        
        context = self.controller.determine_conversation_action(lead, extracted_info, message)
        
        assert context.action == ConversationAction.REQUEST_AVAILABILITY

    def test_determine_conversation_action_ready_for_agent(self):
        """Test conversation action determination for leads ready for agent"""
        lead = Lead(phone="+1234567890", chat_history="Previous conversation")
        # Mock qualified lead with tour availability
        lead.beds = "2"
        lead.baths = "1"
        lead.price = "2000"
        lead.location = "Boston"
        lead.move_in_date = "July 1"
        lead.amenities = "Parking"
        lead.tour_availability = "Weekends"
        
        extracted_info = {}
        message = "I'm available weekends"
        
        context = self.controller.determine_conversation_action(lead, extracted_info, message)
        
        assert context.action == ConversationAction.READY_FOR_AGENT

    def test_format_known_info(self):
        """Test formatting known information"""
        lead = Lead(phone="+1234567890", beds="2", baths="1", price="2000")
        
        result = self.controller._format_known_info(lead)
        
        assert "beds: 2" in result
        assert "baths: 1" in result
        assert "price: 2000" in result

    def test_format_missing_fields(self):
        """Test formatting missing fields"""
        missing_fields = ["move_in_date", "price", "beds"]
        
        result = self.controller._format_missing_fields(missing_fields)
        
        assert "move-in date" in result
        assert "budget" in result
        assert "bedrooms" in result

    def test_get_logical_next_questions(self):
        """Test getting logical next questions"""
        lead = Lead(phone="+1234567890")
        lead.beds = None
        lead.baths = None
        lead.price = None
        lead.location = None
        
        result = self.controller._get_logical_next_questions(lead)
        
        # Should group beds and baths together
        assert "bedrooms and bathrooms" in result

    def test_acknowledge_progress(self):
        """Test acknowledging progress"""
        analysis = ExtractionAnalysis(
            has_new_data=True,
            is_unclear=False,
            unclear_fields=[],
            newly_extracted={"price": "2000", "location": "Boston"},
            extraction_confidence=1.0
        )
        
        result = self.controller._acknowledge_progress(analysis)
        
        assert "budget: 2000" in result
        assert "area: Boston" in result

    def test_format_qualification_summary(self):
        """Test formatting qualification summary"""
        lead = Lead(phone="+1234567890", beds="2", baths="1", price="2000", location="Boston")
        
        result = self.controller._format_qualification_summary(lead)
        
        assert "2 bed, 1 bath" in result
        assert "budget: 2000" in result
        assert "area: Boston" in result

    def test_has_been_summarized(self):
        """Test checking if lead has been summarized"""
        # Lead without optional fields or tour availability
        lead1 = Lead(phone="+1234567890", beds="2", baths="1", price="2000")
        assert self.controller._has_been_summarized(lead1) is False
        
        # Lead with optional field filled
        lead2 = Lead(phone="+1234567890", beds="2", baths="1", price="2000", boston_rental_experience="Yes")
        assert self.controller._has_been_summarized(lead2) is True
        
        # Lead with tour availability
        lead3 = Lead(phone="+1234567890", beds="2", baths="1", price="2000", tour_availability="Weekends")
        assert self.controller._has_been_summarized(lead3) is True

    def test_has_confirmed_summary(self):
        """Test checking if lead has confirmed the summary"""
        # Lead with no chat history
        lead1 = Lead(phone="+1234567890")
        assert self.controller._has_confirmed_summary(lead1) is False
        
        # Lead with confirmation message
        lead2 = Lead(phone="+1234567890", chat_history="User: looks good\nAI: Great!")
        assert self.controller._has_confirmed_summary(lead2) is True
        
        # Lead with other message (no confirmation)
        lead3 = Lead(phone="+1234567890", chat_history="User: I need more info\nAI: Sure!")
        assert self.controller._has_confirmed_summary(lead3) is False

    def test_has_completed_optional_questions(self):
        """Test checking if lead has completed optional questions"""
        # Lead with no optional field and no agent ready message
        lead1 = Lead(phone="+1234567890")
        assert self.controller._has_completed_optional_questions(lead1) is False
        
        # Lead with optional field filled
        lead2 = Lead(phone="+1234567890", boston_rental_experience="Yes")
        assert self.controller._has_completed_optional_questions(lead2) is True
        
        # Lead with agent ready message
        lead3 = Lead(phone="+1234567890", chat_history="AI: ready to send your information to my human agent")
        assert self.controller._has_completed_optional_questions(lead3) is True

    def test_has_been_told_ready_for_agent(self):
        """Test checking if lead has been told they're ready for agent"""
        # Lead with no chat history
        lead1 = Lead(phone="+1234567890")
        assert self.controller._has_been_told_ready_for_agent(lead1) is False
        
        # Lead with agent ready message
        lead2 = Lead(phone="+1234567890", chat_history="AI: ready to send your information to my human agent")
        assert self.controller._has_been_told_ready_for_agent(lead2) is True
        
        # Lead with other message (no agent ready)
        lead3 = Lead(phone="+1234567890", chat_history="AI: Great!")
        assert self.controller._has_been_told_ready_for_agent(lead3) is False

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from src.services.ai.openai_service import OpenAIService
from src.models.lead import Lead


class TestOpenAIService:
    """Test cases for OpenAIService AI functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'gpt-4o-mini'}):
            self.ai_service = OpenAIService()
    
    def test_init_missing_api_key(self):
        """Test initialization with missing API key"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Missing OPENAI_API_KEY environment variable"):
                OpenAIService()
    
    def test_init_with_default_model(self):
        """Test initialization with default model"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            service = OpenAIService()
            assert service.model == "gpt-4o-mini"
    
    def test_init_with_custom_model(self):
        """Test initialization with custom model"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'gpt-4'}):
            service = OpenAIService()
            assert service.model == "gpt-4"
    
    def test_get_database_status(self):
        """Test generating database status string"""
        lead_data = {
            "move_in_date": "2024-02-01",
            "price": "2000",
            "beds": "2",
            "baths": "1",
            "location": "Boston",
            "amenities": "Parking",
            "rental_urgency": "High",
            "boston_rental_experience": "First time"
        }
        
        status = self.ai_service._get_database_status(lead_data)
        
        # Check that all required fields are present
        assert "move_in_date: ✓ HAS DATA" in status
        assert "price: ✓ HAS DATA" in status
        assert "beds: ✓ HAS DATA" in status
        assert "baths: ✓ HAS DATA" in status
        assert "location: ✓ HAS DATA" in status
        assert "amenities: ✓ HAS DATA" in status
        
        # Check that optional fields are present
        assert "OPTIONAL FIELDS:" in status
        assert "rental_urgency: ✓ HAS DATA" in status
        assert "boston_rental_experience: ✓ HAS DATA" in status
    
    def test_get_database_status_missing_fields(self):
        """Test generating database status string with missing fields"""
        lead_data = {
            "move_in_date": "2024-02-01",
            "price": "",
            "beds": "2",
            "baths": "",
            "location": "Boston",
            "amenities": "",
            "rental_urgency": "",
            "boston_rental_experience": "First time"
        }
        
        status = self.ai_service._get_database_status(lead_data)
        
        # Check that missing required fields are marked
        assert "price: ✗ MISSING" in status
        assert "baths: ✗ MISSING" in status
        assert "amenities: ✗ MISSING" in status
        
        # Check that present required fields are marked
        assert "move_in_date: ✓ HAS DATA" in status
        assert "beds: ✓ HAS DATA" in status
        assert "location: ✓ HAS DATA" in status
        
        # Check that optional fields are marked appropriately
        assert "rental_urgency: ○ OPTIONAL" in status
        assert "boston_rental_experience: ✓ HAS DATA" in status
    
    def test_get_chat_history_with_history(self):
        """Test getting chat history when history exists"""
        lead_data = {
            "chat_history": "2024-01-01 10:00 - Lead: Hi there\n2024-01-01 10:01 - AI: Hello!"
        }
        
        history = self.ai_service._get_chat_history(lead_data)
        
        assert "2024-01-01 10:00 - Lead: Hi there" in history
        assert "2024-01-01 10:01 - AI: Hello!" in history
    
    def test_get_chat_history_no_history(self):
        """Test getting chat history when no history exists"""
        lead_data = {"chat_history": ""}
        
        history = self.ai_service._get_chat_history(lead_data)
        
        assert history == "No conversation history yet"
    
    def test_get_chat_history_long_history(self):
        """Test getting chat history when history is very long"""
        # Create a long chat history (more than 10 lines)
        long_history = "\n".join([
            f"2024-01-01 10:{i:02d} - Lead: Message {i}" for i in range(15)
        ])
        
        lead_data = {"chat_history": long_history}
        
        history = self.ai_service._get_chat_history(lead_data)
        
        # Should only include last 10 messages
        lines = history.split("\n")
        assert len(lines) == 10
        assert "Message 0" not in history  # Should be truncated (first 5 messages)
        assert "Message 5" in history  # Should be included (last 10 messages start from 5)
        assert "Message 14" in history  # Should be included
    
    def test_get_phase_instructions_qualification_phase(self):
        """Test getting phase instructions for qualification phase"""
        missing_fields = ["price", "beds"]
        missing_optional = []
        
        phase, instructions = self.ai_service._get_phase_instructions(
            needs_tour_availability=False,
            missing_fields=missing_fields,
            missing_optional=missing_optional
        )
        
        assert "QUALIFICATION" in phase
        assert "price" in instructions
        assert "beds" in instructions
    
    def test_get_phase_instructions_tour_scheduling_phase(self):
        """Test getting phase instructions for tour scheduling phase"""
        missing_fields = []
        missing_optional = []
        
        phase, instructions = self.ai_service._get_phase_instructions(
            needs_tour_availability=True,
            missing_fields=missing_fields,
            missing_optional=missing_optional
        )
        
        assert "TOUR_SCHEDULING" in phase
    
    def test_get_phase_instructions_optional_questions_phase(self):
        """Test getting phase instructions for optional questions phase"""
        missing_fields = []
        missing_optional = ["rental_urgency", "boston_rental_experience"]
        
        phase, instructions = self.ai_service._get_phase_instructions(
            needs_tour_availability=False,
            missing_fields=missing_fields,
            missing_optional=missing_optional
        )
        
        assert "OPTIONAL_QUESTIONS" in phase
        assert "rental_urgency" in instructions
        assert "boston_rental_experience" in instructions
    
    def test_get_phase_instructions_complete_phase(self):
        """Test getting phase instructions for complete phase"""
        missing_fields = []
        missing_optional = []
        
        phase, instructions = self.ai_service._get_phase_instructions(
            needs_tour_availability=False,
            missing_fields=missing_fields,
            missing_optional=missing_optional
        )
        
        assert "COMPLETE" in phase
    
    @pytest.mark.asyncio
    async def test_extract_lead_info_success(self):
        """Test successful lead information extraction"""
        message = "I'm looking for a 2 bedroom apartment for $2000 in Boston"
        lead = Lead(phone="+1234567890")
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "beds": "2",
            "price": "2000",
            "location": "Boston"
        })
        
        self.ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = await self.ai_service.extract_lead_info(message, lead)
        
        assert result["beds"] == "2"
        assert result["price"] == "2000"
        assert result["location"] == "Boston"
        
        # Verify OpenAI was called correctly
        self.ai_service.client.chat.completions.create.assert_called_once()
        call_args = self.ai_service.client.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-4o-mini"
        assert call_args[1]["max_tokens"] == 300
        assert call_args[1]["temperature"] == 0.1
    
    @pytest.mark.asyncio
    async def test_extract_lead_info_openai_error(self):
        """Test lead information extraction when OpenAI fails"""
        message = "I'm looking for an apartment"
        lead = Lead(phone="+1234567890")
        
        # Mock OpenAI to raise an exception
        self.ai_service.client.chat.completions.create = Mock(side_effect=Exception("OpenAI error"))
        
        result = await self.ai_service.extract_lead_info(message, lead)
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_extract_lead_info_none_content(self):
        """Test lead information extraction when OpenAI returns None content"""
        message = "I'm looking for an apartment"
        lead = Lead(phone="+1234567890")
        
        # Mock OpenAI response with None content
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        
        self.ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = await self.ai_service.extract_lead_info(message, lead)
        
        # Should return empty dict when OpenAI returns None content
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_extract_lead_info_invalid_json(self):
        """Test lead information extraction when OpenAI returns invalid JSON"""
        message = "I'm looking for an apartment"
        lead = Lead(phone="+1234567890")
        
        # Mock OpenAI response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "invalid json"
        
        self.ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = await self.ai_service.extract_lead_info(message, lead)
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """Test successful response generation"""
        lead = Lead(
            phone="+1234567890",
            move_in_date="2024-02-01",
            price="2000",
            beds="2",
            baths="1",
            location="Boston",
            amenities="Parking"
        )
        message = "What's your budget?"
        missing_fields = []
        needs_tour_availability = False
        missing_optional = []
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "My budget is $2000 per month."
        
        self.ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = await self.ai_service.generate_response(
            lead, message, missing_fields, needs_tour_availability, missing_optional
        )
        
        assert result == "My budget is $2000 per month."
        
        # Verify OpenAI was called correctly
        self.ai_service.client.chat.completions.create.assert_called_once()
        call_args = self.ai_service.client.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-4o-mini"
        assert call_args[1]["max_tokens"] == 300
        assert call_args[1]["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_generate_response_openai_error(self):
        """Test response generation when OpenAI fails"""
        lead = Lead(phone="+1234567890")
        message = "Hello"
        missing_fields = []
        needs_tour_availability = False
        missing_optional = []
        
        # Mock OpenAI to raise an exception
        self.ai_service.client.chat.completions.create = Mock(side_effect=Exception("OpenAI error"))
        
        result = await self.ai_service.generate_response(
            lead, message, missing_fields, needs_tour_availability, missing_optional
        )
        
        assert result == "I'm having trouble processing your message. Please try again."
    
    @pytest.mark.asyncio
    async def test_generate_response_none_content(self):
        """Test response generation when OpenAI returns None content"""
        lead = Lead(phone="+1234567890")
        message = "Hello"
        missing_fields = []
        needs_tour_availability = False
        missing_optional = []
        
        # Mock OpenAI response with None content
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        
        self.ai_service.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = await self.ai_service.generate_response(
            lead, message, missing_fields, needs_tour_availability, missing_optional
        )
        
        # Should return fallback message when OpenAI returns None content
        assert result == "I'm having trouble processing your message. Please try again."
    
    @pytest.mark.asyncio
    async def test_generate_delay_response_success(self):
        """Test successful delay response generation"""
        delay_info = {"delay_days": 3}
        
        result = await self.ai_service.generate_delay_response(delay_info)
        
        assert "3 days" in result
        assert "I'll reach out" in result
    
    @pytest.mark.asyncio
    async def test_generate_delay_response_one_day(self):
        """Test delay response generation for one day"""
        delay_info = {"delay_days": 1}
        
        result = await self.ai_service.generate_delay_response(delay_info)
        
        assert "tomorrow" in result
    
    @pytest.mark.asyncio
    async def test_generate_delay_response_weeks(self):
        """Test delay response generation for weeks"""
        delay_info = {"delay_days": 14}
        
        result = await self.ai_service.generate_delay_response(delay_info)
        
        assert "2 weeks" in result
    
    @pytest.mark.asyncio
    async def test_generate_delay_response_months(self):
        """Test delay response generation for months"""
        delay_info = {"delay_days": 60}
        
        result = await self.ai_service.generate_delay_response(delay_info)
        
        assert "2 months" in result
    
    @pytest.mark.asyncio
    async def test_generate_delay_response_error(self):
        """Test delay response generation when error occurs"""
        delay_info = {"invalid": "data"}
        
        result = await self.ai_service.generate_delay_response(delay_info)
        
        assert "I'll follow up with you later" in result

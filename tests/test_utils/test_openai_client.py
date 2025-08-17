import pytest
from unittest.mock import patch, Mock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


@patch.dict(os.environ, {"OPENAI_API_KEY": "test_key", "OPENAI_MODEL": "gpt-4o-mini"})
class TestOpenAIClient:
    @patch("src.utils.openai_client.openai.OpenAI")
    def test_init_success(self, mock_openai):
        """Test successful initialization of OpenAI client"""
        from src.utils.openai_client import OpenAIClient

        client = OpenAIClient()

        mock_openai.assert_called_once_with(api_key="test_key")
        assert client.model == "gpt-4o-mini"

    def test_init_missing_api_key(self):
        """Test initialization failure when API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            from src.utils.openai_client import OpenAIClient

            with pytest.raises(ValueError) as exc_info:
                OpenAIClient()

            assert "Missing OPENAI_API_KEY environment variable" in str(exc_info.value)

    @patch("src.utils.openai_client.openai.OpenAI")
    def test_get_database_status(self, mock_openai):
        """Test database status generation"""
        from src.utils.openai_client import OpenAIClient

        client = OpenAIClient()
        lead_data = {
            "move_in_date": "2024-01-01",
            "price": "",
            "beds": "2",
            "baths": None,
            "location": "Boston",
            "amenities": "",
            "rental_urgency": "high",
            "boston_rental_experience": "",
        }

        status = client._get_database_status(lead_data)

        assert "✓ HAS DATA" in status
        assert "✗ MISSING" in status
        assert "move_in_date: ✓ HAS DATA (2024-01-01)" in status
        assert "price: ✗ MISSING (empty)" in status

    @patch("src.utils.openai_client.openai.OpenAI")
    def test_get_chat_history(self, mock_openai):
        """Test chat history formatting"""
        from src.utils.openai_client import OpenAIClient

        client = OpenAIClient()
        lead_data = {"chat_history": "Line 1\nLine 2\nLine 3"}

        history = client._get_chat_history(lead_data)

        assert history == "Line 1\nLine 2\nLine 3"

    @patch("src.utils.openai_client.openai.OpenAI")
    def test_get_chat_history_empty(self, mock_openai):
        """Test chat history when empty"""
        from src.utils.openai_client import OpenAIClient

        client = OpenAIClient()
        lead_data = {}

        history = client._get_chat_history(lead_data)

        assert history == "No conversation history yet"

    @patch("src.utils.openai_client.openai.OpenAI")
    def test_generate_response_success(self, mock_openai):
        """Test successful response generation"""
        from src.utils.openai_client import OpenAIClient

        # Setup mock
        mock_client = mock_openai.return_value
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        lead_data = {
            "move_in_date": "2024-01-01",
            "chat_history": "Previous conversation",
        }

        response = client.generate_response(
            lead_data=lead_data,
            incoming_message="Test message",
            missing_fields=["price"],
            needs_tour_availability=False,
        )

        assert response == "Test response"
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.utils.openai_client.openai.OpenAI")
    def test_generate_response_none_content(self, mock_openai):
        """Test response generation when OpenAI returns None content"""
        from src.utils.openai_client import OpenAIClient

        # Setup mock
        mock_client = mock_openai.return_value
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        lead_data = {"move_in_date": "2024-01-01"}

        with pytest.raises(ValueError) as exc_info:
            client.generate_response(
                lead_data=lead_data,
                incoming_message="Test message",
                missing_fields=["price"],
            )

        assert "OpenAI returned None content" in str(exc_info.value)

    @patch("src.utils.openai_client.openai.OpenAI")
    def test_generate_response_exception_fallback(self, mock_openai):
        """Test response generation fallback on exception"""
        from src.utils.openai_client import OpenAIClient

        # Setup mock to raise exception
        mock_client = mock_openai.return_value
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        client = OpenAIClient()
        lead_data = {"move_in_date": "2024-01-01"}

        response = client.generate_response(
            lead_data=lead_data,
            incoming_message="Test message",
            missing_fields=["price"],
        )

        assert (
            response
            == "Thanks for your message. Our agent will follow up with you soon."
        )

    @patch("src.utils.openai_client.openai.OpenAI")
    def test_extract_lead_info_success(self, mock_openai):
        """Test successful lead info extraction"""
        from src.utils.openai_client import OpenAIClient

        # Setup mock
        mock_client = mock_openai.return_value
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"beds": "2", "location": "Boston"}'
        mock_client.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        current_data = {"move_in_date": "2024-01-01"}

        result = client.extract_lead_info(
            "Looking for 2 bedroom in Boston", current_data
        )

        assert result == {"beds": "2", "location": "Boston"}
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.utils.openai_client.openai.OpenAI")
    def test_extract_lead_info_json_error(self, mock_openai):
        """Test lead info extraction with JSON parsing error"""
        from src.utils.openai_client import OpenAIClient

        # Setup mock
        mock_client = mock_openai.return_value
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON"
        mock_client.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        current_data = {"move_in_date": "2024-01-01"}

        result = client.extract_lead_info(
            "Looking for 2 bedroom in Boston", current_data
        )

        assert result == {}

    @patch("src.utils.openai_client.openai.OpenAI")
    def test_extract_lead_info_none_content(self, mock_openai):
        """Test lead info extraction when OpenAI returns None content"""
        from src.utils.openai_client import OpenAIClient

        # Setup mock
        mock_client = mock_openai.return_value
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        current_data = {"move_in_date": "2024-01-01"}

        result = client.extract_lead_info(
            "Looking for 2 bedroom in Boston", current_data
        )

        assert result == {}

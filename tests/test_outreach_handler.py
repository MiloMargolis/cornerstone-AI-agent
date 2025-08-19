import json
import pytest
from unittest.mock import MagicMock, patch, Mock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@patch.dict(
    os.environ,
    {
        "TELNYX_API_KEY": "test_key",
        "TELNYX_PHONE_NUMBER": "+1234567890",
        "OPENAI_API_KEY": "test_key",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "AGENT_PHONE_NUMBER": "+1987654321",
        "OPENAI_MODEL": "gpt-4o-mini",
    },
)
class TestOutreachHandler:
    def test_validate_phone_number_with_country_code(self):
        """Test phone number validation with country code"""
        from src.outreach_handler import validate_phone_number

        assert validate_phone_number("+12345678901") == "+12345678901"
        assert validate_phone_number("12345678901") == "+12345678901"
        assert validate_phone_number("1-234-567-8901") == "+12345678901"

    def test_validate_phone_number_without_country_code(self):
        """Test phone number validation without country code"""
        from src.outreach_handler import validate_phone_number

        assert validate_phone_number("2345678901") == "+12345678901"
        assert validate_phone_number("234-567-8901") == "+12345678901"
        assert validate_phone_number("(234) 567-8901") == "+12345678901"

    def test_validate_phone_number_invalid(self):
        """Test phone number validation with invalid numbers"""
        from src.outreach_handler import validate_phone_number

        assert validate_phone_number("123456789") is None  # Too short
        assert validate_phone_number("123456789012") is None  # Too long
        assert validate_phone_number("22345678901") is None  # Invalid country code
        assert validate_phone_number("abc-def-ghij") is None  # Non-numeric

    @patch("src.outreach_handler.supabase_client.get_lead_by_phone")
    def test_check_if_phone_number_exists_true(self, mock_get_lead):
        """Test checking if phone number exists - returns True"""
        from src.outreach_handler import check_if_phone_number_exists

        mock_get_lead.return_value = {"phone": "+1234567890"}

        result = check_if_phone_number_exists("+1234567890")

        assert result is True
        mock_get_lead.assert_called_once_with("+1234567890")

    @patch("src.outreach_handler.supabase_client.get_lead_by_phone")
    def test_check_if_phone_number_exists_false(self, mock_get_lead):
        """Test checking if phone number exists - returns False"""
        from src.outreach_handler import check_if_phone_number_exists

        mock_get_lead.return_value = None

        result = check_if_phone_number_exists("+1234567890")

        assert result is False
        mock_get_lead.assert_called_once_with("+1234567890")

    @patch("src.outreach_handler.supabase_client.get_lead_by_phone")
    def test_check_if_phone_number_exists_exception(self, mock_get_lead):
        """Test checking if phone number exists - handles exception"""
        from src.outreach_handler import check_if_phone_number_exists

        mock_get_lead.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            check_if_phone_number_exists("+1234567890")

        assert "Failed to check phone number in database" in str(exc_info.value)

    @patch("src.outreach_handler.supabase_client.create_lead")
    def test_call_create_lead_success(self, mock_create_lead):
        """Test successful lead creation"""
        from src.outreach_handler import call_create_lead

        expected_lead = {"phone": "+1234567890", "name": "John Doe"}
        mock_create_lead.return_value = expected_lead

        result = call_create_lead("+1234567890", "John Doe", "Initial message")

        assert result == expected_lead
        mock_create_lead.assert_called_once_with(
            phone="+1234567890", name="John Doe", initial_message="Initial message"
        )

    @patch("src.outreach_handler.supabase_client.create_lead")
    def test_call_create_lead_failure(self, mock_create_lead):
        """Test lead creation failure"""
        from src.outreach_handler import call_create_lead

        mock_create_lead.return_value = None

        with pytest.raises(Exception) as exc_info:
            call_create_lead("+1234567890", "John Doe", "Initial message")

        assert "Failed to create lead record" in str(exc_info.value)

    @patch("src.outreach_handler.supabase_client")
    @patch("src.outreach_handler.telnyx_client.send_sms")
    def test_send_initial_outreach_message_success(self, mock_send_sms, mock_supabase):
        """Test successful sending of initial outreach message"""
        from src.outreach_handler import send_initial_outreach_message

        lead = {"name": "John Doe", "phone": "+1234567890"}
        mock_supabase.get_missing_fields.return_value = []
        mock_supabase.needs_tour_availability.return_value = False
        mock_supabase.get_missing_optional_fields.return_value = []
        mock_send_sms.return_value = True

        result = send_initial_outreach_message(lead, "+1234567890")

        assert result is True
        mock_send_sms.assert_called_once()
        call_args = mock_send_sms.call_args
        assert call_args[0][0] == "+1234567890"
        assert "Hi John" in call_args[0][1]
        assert "Paloma from Cornerstone Real Estate" in call_args[0][1]

    @patch("src.outreach_handler.supabase_client")
    @patch("src.outreach_handler.telnyx_client.send_sms")
    def test_send_initial_outreach_message_no_name(self, mock_send_sms, mock_supabase):
        """Test sending initial outreach message without name"""
        from src.outreach_handler import send_initial_outreach_message

        lead = {"phone": "+1234567890"}  # No name
        mock_supabase.get_missing_fields.return_value = []
        mock_supabase.needs_tour_availability.return_value = False
        mock_supabase.get_missing_optional_fields.return_value = []
        mock_send_sms.return_value = True

        result = send_initial_outreach_message(lead, "+1234567890")

        assert result is True
        call_args = mock_send_sms.call_args
        assert not call_args[0][1].startswith("Hi ")
        assert "my name is Paloma" in call_args[0][1]

    @patch("src.outreach_handler.check_if_phone_number_exists")
    @patch("src.outreach_handler.call_create_lead")
    @patch("src.outreach_handler.send_initial_outreach_message")
    def test_lambda_handler_success(
        self, mock_send_message, mock_create_lead, mock_check_exists
    ):
        """Test successful outreach handler execution"""
        from src.outreach_handler import lambda_handler

        event = {"phone_number": "234-567-8901", "name": "John Doe"}

        mock_check_exists.return_value = False
        mock_create_lead.return_value = {"phone": "+12345678901", "name": "John Doe"}
        mock_send_message.return_value = True

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["message"] == "Initial outreach message sent successfully"

    def test_lambda_handler_missing_phone_number(self):
        """Test handler with missing phone number"""
        from src.outreach_handler import lambda_handler

        event = {"name": "John Doe"}  # Missing phone_number

        result = lambda_handler(event, None)

        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "Missing required field: phone_number" in response_data["error"]

    def test_lambda_handler_missing_name(self):
        """Test handler with missing name"""
        from src.outreach_handler import lambda_handler

        event = {"phone_number": "+1234567890"}  # Missing name

        result = lambda_handler(event, None)

        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "Missing required field: name" in response_data["error"]

    def test_lambda_handler_invalid_phone_format(self):
        """Test handler with invalid phone number format"""
        from src.outreach_handler import lambda_handler

        event = {"phone_number": "123", "name": "John Doe"}  # Invalid format

        result = lambda_handler(event, None)

        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "Invalid phone number format" in response_data["error"]

    @patch("src.outreach_handler.check_if_phone_number_exists")
    def test_lambda_handler_phone_already_exists(self, mock_check_exists):
        """Test handler when phone number already exists"""
        from src.outreach_handler import lambda_handler

        event = {"phone_number": "234-567-8901", "name": "John Doe"}

        mock_check_exists.return_value = True

        result = lambda_handler(event, None)

        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "Phone number already exists in the database" in response_data["error"]

    @patch("src.outreach_handler.check_if_phone_number_exists")
    @patch("src.outreach_handler.call_create_lead")
    @patch("src.outreach_handler.send_initial_outreach_message")
    def test_lambda_handler_send_message_failure(
        self, mock_send_message, mock_create_lead, mock_check_exists
    ):
        """Test handler when sending message fails"""
        from src.outreach_handler import lambda_handler

        event = {"phone_number": "234-567-8901", "name": "John Doe"}

        mock_check_exists.return_value = False
        mock_create_lead.return_value = {"phone": "+12345678901", "name": "John Doe"}
        mock_send_message.return_value = False  # Message sending fails

        result = lambda_handler(event, None)

        assert result["statusCode"] == 500
        response_data = json.loads(result["body"])
        assert "Failed to send initial outreach message" in response_data["error"]

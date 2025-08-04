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
        "SUPABASE_KEY": "test_key",
        "AGENT_PHONE_NUMBER": "+1987654321",
        "OPENAI_MODEL": "gpt-4o-mini",
    },
)
class TestFollowUpHandler:

    @patch("src.follow_up_handler.SupabaseClient")
    @patch("src.follow_up_handler.TelnyxClient")
    def test_lambda_handler_success(self, mock_telnyx, mock_supabase):
        """Test successful follow-up processing"""
        from src.follow_up_handler import lambda_handler

        # Setup mocks
        mock_supabase_instance = mock_supabase.return_value
        mock_telnyx_instance = mock_telnyx.return_value

        leads_needing_followup = [
            {"phone": "+1234567890", "follow_up_count": 0, "follow_up_stage": "first"},
            {"phone": "+1234567891", "follow_up_count": 1, "follow_up_stage": "second"},
        ]

        mock_supabase_instance.get_leads_needing_follow_up.return_value = (
            leads_needing_followup
        )
        mock_telnyx_instance.send_sms.return_value = True
        mock_supabase_instance.increment_follow_up_count.return_value = True
        mock_supabase_instance.schedule_follow_up.return_value = True

        # Call the handler
        result = lambda_handler({}, None)

        # Assertions
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["message"] == "Follow-up processing completed"
        assert response_data["successful_follow_ups"] == 2
        assert response_data["failed_follow_ups"] == 0
        assert response_data["total_leads_processed"] == 2

        # Verify method calls
        assert mock_telnyx_instance.send_sms.call_count == 2
        assert mock_supabase_instance.increment_follow_up_count.call_count == 2

    @patch("src.follow_up_handler.SupabaseClient")
    @patch("src.follow_up_handler.TelnyxClient")
    def test_lambda_handler_no_leads(self, mock_telnyx, mock_supabase):
        """Test when no leads need follow-up"""
        from src.follow_up_handler import lambda_handler

        # Setup mocks
        mock_supabase_instance = mock_supabase.return_value
        mock_supabase_instance.get_leads_needing_follow_up.return_value = []

        # Call the handler
        result = lambda_handler({}, None)

        # Assertions
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["successful_follow_ups"] == 0
        assert response_data["total_leads_processed"] == 0

    @patch("src.follow_up_handler.SupabaseClient")
    @patch("src.follow_up_handler.TelnyxClient")
    @patch(
        "src.follow_up_handler.FOLLOW_UP_MESSAGES", {"first": "First follow-up message"}
    )
    def test_process_follow_up_success(self, mock_telnyx, mock_supabase):
        """Test successful processing of a single follow-up"""
        from src.follow_up_handler import process_follow_up

        # Setup mocks
        mock_supabase_instance = mock_supabase.return_value
        mock_telnyx_instance = mock_telnyx.return_value

        lead = {
            "phone": "+1234567890",
            "follow_up_count": 0,
            "follow_up_stage": "first",
        }

        mock_telnyx_instance.send_sms.return_value = True
        mock_supabase_instance.increment_follow_up_count.return_value = True
        mock_supabase_instance.schedule_follow_up.return_value = True

        # Call the function
        result = process_follow_up(lead, mock_supabase_instance, mock_telnyx_instance)

        # Assertions
        assert result is True
        mock_telnyx_instance.send_sms.assert_called_once_with(
            "+1234567890", "First follow-up message"
        )
        mock_supabase_instance.add_message_to_history.assert_called_once()
        mock_supabase_instance.increment_follow_up_count.assert_called_once()

    @patch("src.follow_up_handler.SupabaseClient")
    @patch("src.follow_up_handler.TelnyxClient")
    def test_process_follow_up_sms_failure(self, mock_telnyx, mock_supabase):
        """Test follow-up processing when SMS sending fails"""
        from src.follow_up_handler import process_follow_up

        # Setup mocks
        mock_supabase_instance = mock_supabase.return_value
        mock_telnyx_instance = mock_telnyx.return_value

        lead = {
            "phone": "+1234567890",
            "follow_up_count": 0,
            "follow_up_stage": "first",
        }

        mock_telnyx_instance.send_sms.return_value = False  # SMS sending fails

        # Call the function
        result = process_follow_up(lead, mock_supabase_instance, mock_telnyx_instance)

        # Assertions
        assert result is False
        mock_supabase_instance.increment_follow_up_count.assert_not_called()

    @patch("src.follow_up_handler.SupabaseClient")
    @patch("src.follow_up_handler.TelnyxClient")
    @patch("src.follow_up_handler.MAX_FOLLOW_UPS", 3)
    def test_process_follow_up_max_reached(self, mock_telnyx, mock_supabase):
        """Test follow-up processing when max follow-ups is reached"""
        from src.follow_up_handler import process_follow_up

        # Setup mocks
        mock_supabase_instance = mock_supabase.return_value
        mock_telnyx_instance = mock_telnyx.return_value

        lead = {
            "phone": "+1234567890",
            "follow_up_count": 2,  # Will be 3 after increment, reaching max
            "follow_up_stage": "final",
        }

        mock_telnyx_instance.send_sms.return_value = True
        mock_supabase_instance.increment_follow_up_count.return_value = True

        # Call the function
        result = process_follow_up(lead, mock_supabase_instance, mock_telnyx_instance)

        # Assertions
        assert result is True
        mock_supabase_instance.schedule_follow_up.assert_not_called()  # No next follow-up scheduled

    def test_process_follow_up_no_phone(self):
        """Test follow-up processing when lead has no phone number"""
        from src.follow_up_handler import process_follow_up

        lead = {
            "follow_up_count": 0,
            "follow_up_stage": "first",
            # Missing 'phone' field
        }

        result = process_follow_up(lead, Mock(), Mock())

        assert result is False

    @patch("src.follow_up_handler.SupabaseClient")
    @patch("src.follow_up_handler.TelnyxClient")
    def test_lambda_handler_partial_failures(self, mock_telnyx, mock_supabase):
        """Test handler when some follow-ups succeed and some fail"""
        from src.follow_up_handler import lambda_handler

        # Setup mocks
        mock_supabase_instance = mock_supabase.return_value
        mock_telnyx_instance = mock_telnyx.return_value

        leads_needing_followup = [
            {"phone": "+1234567890", "follow_up_count": 0, "follow_up_stage": "first"},
            {"phone": "+1234567891", "follow_up_count": 1, "follow_up_stage": "second"},
            {
                "follow_up_count": 0,
                "follow_up_stage": "first",
            },  # Missing phone - will fail
        ]

        mock_supabase_instance.get_leads_needing_follow_up.return_value = (
            leads_needing_followup
        )
        mock_telnyx_instance.send_sms.return_value = True
        mock_supabase_instance.increment_follow_up_count.return_value = True
        mock_supabase_instance.schedule_follow_up.return_value = True

        # Call the handler
        result = lambda_handler({}, None)

        # Assertions
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["successful_follow_ups"] == 2
        assert response_data["failed_follow_ups"] == 1
        assert response_data["total_leads_processed"] == 3

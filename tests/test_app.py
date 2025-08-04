import json
from unittest import mock
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
        "TELNYX_PHONE_NUMBER": "+1555000000",
        "OPENAI_API_KEY": "test_key",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test_key",
        "AGENT_PHONE_NUMBER": "+1987654321",
        "OPENAI_MODEL": "gpt-4o-mini",
        "MOCK_TELNX": "1",
    },
)
class TestSMSHandler:

    @patch("src.app.SupabaseClient")
    @patch("src.app.OpenAIClient")
    @patch("src.app.TelnyxClient")
    @patch("src.app.DelayDetector")
    def test_lambda_handler_message_received_success(
        self,
        mock_delay_detector,
        mock_telnyx,
        mock_openai,
        mock_supabase,
        sample_webhook_event,
    ):
        """Test successful processing of a received message"""
        # Import after patching environment
        from src.app import lambda_handler

        # Setup mocks
        mock_supabase_instance = mock_supabase.return_value
        mock_openai_instance = mock_openai.return_value
        mock_telnyx_instance = mock_telnyx.return_value
        mock_delay_detector_instance = mock_delay_detector.return_value

        mock_supabase_instance.get_lead_by_phone.return_value = None
        mock_supabase_instance.create_lead.return_value = {
            "phone": "+1234567890",
            "tour_ready": False,
        }
        mock_openai_instance.extract_lead_info.return_value = {
            "beds": "2",
            "location": "Boston",
        }
        mock_supabase_instance.update_lead.return_value = {"phone": "+1234567890"}
        mock_delay_detector_instance.detect_delay_request.return_value = None
        mock_supabase_instance.get_missing_fields.return_value = [
            "price",
            "move_in_date",
        ]
        mock_supabase_instance.needs_tour_availability.return_value = False
        mock_openai_instance.generate_response.return_value = (
            "Thanks for your interest! What's your price range?"
        )
        mock_telnyx_instance.send_sms.return_value = True

        # Call the handler
        result = lambda_handler(sample_webhook_event, None)

        # Assertions
        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["message"] == "Message processed successfully"

        # Verify method calls
        mock_supabase_instance.get_lead_by_phone.assert_called_once_with("+1234567890")
        mock_supabase_instance.create_lead.assert_called_once()
        mock_openai_instance.extract_lead_info.assert_called_once()
        mock_telnyx_instance.send_sms.assert_called_once()

    def test_lambda_handler_ignores_non_message_events(self):
        """Test that non-message events are ignored"""
        from src.app import lambda_handler

        event = {
            "body": json.dumps({"data": {"event_type": "call.received", "payload": {}}})
        }

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["message"] == "Event ignored"

    def test_lambda_handler_ignores_agent_messages(self):
        """Test that messages from the agent are ignored"""
        from src.app import lambda_handler

        event = {
            "body": json.dumps(
                {
                    "data": {
                        "event_type": "message.received",
                        "payload": {
                            "from": {"phone_number": "+1987654321"},  # Agent's number
                            "to": [{"phone_number": "+1234567890"}],
                            "text": "Test message",
                        },
                    }
                }
            )
        }

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        response_data = json.loads(result["body"])
        assert response_data["message"] == "Agent message ignored"

    def test_lambda_handler_missing_message_data(self):
        """Test handling of malformed webhook data"""
        from src.app import lambda_handler

        event = {
            "body": json.dumps(
                {
                    "data": {
                        "event_type": "message.received",
                        "payload": {
                            "from": {"phone_number": "+1234567890"},
                            # Missing 'text' field
                        },
                    }
                }
            )
        }

        result = lambda_handler(event, None)

        assert result["statusCode"] == 400
        response_data = json.loads(result["body"])
        assert "Missing required message data" in response_data["error"]

    @patch("src.app.SupabaseClient")
    @patch("src.app.OpenAIClient")
    @patch("src.app.TelnyxClient")
    @patch("src.app.DelayDetector")
    def test_process_lead_message_tour_ready_stays_silent(
        self, mock_delay_detector, mock_telnyx, mock_openai, mock_supabase
    ):
        """Test that tour_ready leads receive no response (stay silent)"""
        from src.app import process_lead_message

        # Setup mocks
        mock_supabase_instance = mock_supabase.return_value
        mock_delay_detector_instance = mock_delay_detector.return_value

        tour_ready_lead = {
            "phone": "+1234567890",
            "tour_ready": True,
            "beds": "2",
            "location": "Boston",
        }

        mock_supabase_instance.get_lead_by_phone.return_value = tour_ready_lead
        mock_delay_detector_instance.detect_delay_request.return_value = None

        result = process_lead_message("+1234567890", "Any message")

        # Should return the silent indicator
        assert result == "SILENT_TOUR_READY"

        # Should not call SMS sending
        mock_telnyx.return_value.send_sms.assert_not_called()

    @patch("src.app.SupabaseClient")
    @patch("src.app.OpenAIClient")
    @patch("src.app.TelnyxClient")
    @patch("src.app.DelayDetector")
    def test_process_lead_message_delay_request(
        self, mock_delay_detector, mock_telnyx, mock_openai, mock_supabase
    ):
        """Test handling of delay requests"""
        from src.app import process_lead_message

        # Setup mocks
        mock_supabase_instance = mock_supabase.return_value
        mock_delay_detector_instance = mock_delay_detector.return_value
        mock_telnyx_instance = mock_telnyx.return_value

        mock_supabase_instance.get_lead_by_phone.return_value = {
            "phone": "+1234567890",
            "tour_ready": False,
        }
        mock_delay_detector_instance.detect_delay_request.return_value = {
            "delay_days": 3
        }
        mock_delay_detector_instance.calculate_delay_until.return_value = Mock()
        mock_telnyx_instance.send_sms.return_value = True

        result = process_lead_message("+1234567890", "Can you contact me next week?")

        # Verify delay handling
        mock_supabase_instance.pause_follow_up_until.assert_called_once()
        mock_telnyx_instance.send_sms.assert_called_once()
        assert "reach out" in result

    @patch("src.app.SupabaseClient")
    @patch("src.app.OpenAIClient")
    @patch("src.app.TelnyxClient")
    @patch("src.app.DelayDetector")
    def test_process_lead_message_tour_availability_makes_tour_ready(
        self, mock_delay_detector, mock_telnyx, mock_openai, mock_supabase
    ):
        """Test when tour availability is provided and lead becomes tour-ready"""
        from src.app import process_lead_message

        # Setup mocks
        mock_supabase_instance = mock_supabase.return_value
        mock_openai_instance = mock_openai.return_value
        mock_telnyx_instance = mock_telnyx.return_value
        mock_delay_detector_instance = mock_delay_detector.return_value

        # Fully qualified lead missing only tour availability
        qualified_lead_without_tour = {
            "phone": "+1234567890",
            "tour_ready": False,
            "tour_availability": "",
            "move_in_date": "January 2025",
            "price": "2000-3000",
            "beds": "2",
            "baths": "1",
            "location": "Boston",
            "amenities": "parking",
        }

        updated_lead_data = {
            "phone": "+1234567890",
            "tour_ready": False,  # Still False until set_tour_ready is called
            "tour_availability": "weekends",
            "move_in_date": "January 2025",
            "price": "2000-3000",
            "beds": "2",
            "baths": "1",
            "location": "Boston",
            "amenities": "parking",
        }

        mock_supabase_instance.get_lead_by_phone.return_value = (
            qualified_lead_without_tour
        )
        mock_supabase_instance.update_lead.return_value = updated_lead_data
        mock_openai_instance.extract_lead_info.return_value = {
            "tour_availability": "weekends"
        }
        mock_delay_detector_instance.detect_delay_request.return_value = False
        mock_telnyx_instance.send_sms.return_value = True

        result = process_lead_message("+1234567890", "I'm available on weekends")

        # Should set tour_ready and notify agent
        mock_supabase_instance.set_tour_ready.assert_called_once_with("+1234567890")
        mock_telnyx_instance.send_sms.assert_any_call(
            "+1987654321", mock.ANY
        )  # Agent notification
        mock_telnyx_instance.send_sms.assert_any_call(
            "+1234567890", mock.ANY
        )  # Lead response
        assert "Perfect!" in result
        assert "teammate" in result

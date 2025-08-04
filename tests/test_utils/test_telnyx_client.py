import pytest
from unittest.mock import MagicMock, patch, Mock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


@patch.dict(
    os.environ, {"TELNYX_API_KEY": "test_key", "TELNYX_PHONE_NUMBER": "+1234567890"}
)
class TestTelnyxClient:

    @patch("src.utils.telnyx_client.telnyx")
    def test_init_success(self, mock_telnyx):
        """Test successful initialization of Telnyx client"""
        from src.utils.telnyx_client import TelnyxClient

        client = TelnyxClient()

        assert mock_telnyx.api_key == "test_key"
        assert client.from_number == "+1234567890"

    def test_init_missing_api_key(self):
        """Test initialization failure when API key is missing"""
        with patch.dict(os.environ, {"TELNYX_PHONE_NUMBER": "+1234567890"}, clear=True):
            from src.utils.telnyx_client import TelnyxClient

            with pytest.raises(ValueError) as exc_info:
                TelnyxClient()

            assert "Missing TELNYX_API_KEY environment variable" in str(exc_info.value)

    def test_init_missing_phone_number(self):
        """Test initialization failure when phone number is missing"""
        with patch.dict(os.environ, {"TELNYX_API_KEY": "test_key"}, clear=True):
            from src.utils.telnyx_client import TelnyxClient

            with pytest.raises(ValueError) as exc_info:
                TelnyxClient()

            assert "Missing TELNYX_PHONE_NUMBER environment variable" in str(
                exc_info.value
            )

    @patch("src.utils.telnyx_client.telnyx")
    def test_send_sms_success(self, mock_telnyx):
        """Test successful SMS sending"""
        from src.utils.telnyx_client import TelnyxClient

        # Setup mock
        mock_message = Mock()
        mock_message.id = "msg_12345"
        mock_telnyx.Message.create.return_value = mock_message

        client = TelnyxClient()
        result = client.send_sms("+1987654321", "Test message")

        assert result is True
        mock_telnyx.Message.create.assert_called_once_with(
            from_="+1234567890", to="+1987654321", text="Test message"
        )

    @patch("src.utils.telnyx_client.telnyx")
    def test_send_sms_failure(self, mock_telnyx):
        """Test SMS sending failure"""
        from src.utils.telnyx_client import TelnyxClient

        # Setup mock to raise exception
        mock_telnyx.Message.create.side_effect = Exception("API Error")

        client = TelnyxClient()
        result = client.send_sms("+1987654321", "Test message")

        assert result is False

    @patch("src.utils.telnyx_client.telnyx")
    def test_send_group_sms_success(self, mock_telnyx):
        """Test successful group SMS sending"""
        from src.utils.telnyx_client import TelnyxClient

        # Setup mock
        mock_message = Mock()
        mock_message.id = "msg_12345"
        mock_telnyx.Message.create.return_value = mock_message

        client = TelnyxClient()
        result = client.send_group_sms(["+1987654321", "+1987654322"], "Group message")

        assert result is True
        assert mock_telnyx.Message.create.call_count == 2

    @patch("src.utils.telnyx_client.telnyx")
    def test_send_group_sms_partial_failure(self, mock_telnyx):
        """Test group SMS sending with partial failures"""
        from src.utils.telnyx_client import TelnyxClient

        # Setup mock to succeed first, fail second
        mock_message = Mock()
        mock_message.id = "msg_12345"
        mock_telnyx.Message.create.side_effect = [mock_message, Exception("API Error")]

        client = TelnyxClient()
        result = client.send_group_sms(["+1987654321", "+1987654322"], "Group message")

        assert result is True  # At least one succeeded
        assert mock_telnyx.Message.create.call_count == 2

    @patch("src.utils.telnyx_client.telnyx")
    def test_send_group_sms_all_fail(self, mock_telnyx):
        """Test group SMS sending when all fail"""
        from src.utils.telnyx_client import TelnyxClient

        # Setup mock to fail all calls
        mock_telnyx.Message.create.side_effect = Exception("API Error")

        client = TelnyxClient()
        result = client.send_group_sms(["+1987654321", "+1987654322"], "Group message")

        assert result is False


class TestMockTelnyxClient:

    def test_mock_init_success(self):
        """Test successful initialization of Mock Telnyx client"""
        with patch.dict(os.environ, {"TELNYX_API_KEY": "test_key"}):
            from src.utils.telnyx_client import MockTelnyxClient

            client = MockTelnyxClient()
            assert client.from_number == "test_key"

    def test_mock_init_missing_phone_number(self):
        """Test Mock initialization failure when phone number is missing"""
        with patch.dict(os.environ, {}, clear=True):
            from src.utils.telnyx_client import MockTelnyxClient

            with pytest.raises(ValueError) as exc_info:
                MockTelnyxClient()

            assert "Missing TELNYX_PHONE_NUMBER environment variable" in str(
                exc_info.value
            )

    def test_mock_send_sms(self):
        """Test Mock SMS sending"""
        with patch.dict(os.environ, {"TELNYX_API_KEY": "test_key"}):
            from src.utils.telnyx_client import MockTelnyxClient

            client = MockTelnyxClient()
            result = client.send_sms("+1987654321", "Test message")

            assert result is True

    def test_mock_send_group_sms(self):
        """Test Mock group SMS sending"""
        with patch.dict(os.environ, {"TELNYX_API_KEY": "test_key"}):
            from src.utils.telnyx_client import MockTelnyxClient

            client = MockTelnyxClient()
            result = client.send_group_sms(
                ["+1987654321", "+1987654322"], "Group message"
            )

            assert result is True

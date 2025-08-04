import pytest
from unittest.mock import MagicMock, patch, Mock
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


@patch.dict(
    os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test_key"}
)
class TestSupabaseClient:

    @patch("src.utils.supabase_client.create_client")
    def test_init_success(self, mock_create_client):
        """Test successful initialization of Supabase client"""
        from src.utils.supabase_client import SupabaseClient

        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        client = SupabaseClient()

        mock_create_client.assert_called_once_with(
            "https://test.supabase.co", "test_key"
        )
        assert client.client == mock_client

    def test_init_missing_credentials(self):
        """Test initialization failure when credentials are missing"""
        with patch.dict(os.environ, {}, clear=True):
            from src.utils.supabase_client import SupabaseClient

            with pytest.raises(ValueError) as exc_info:
                SupabaseClient()

            assert "Missing SUPABASE_URL or SUPABASE_KEY environment variables" in str(
                exc_info.value
            )

    @patch("src.utils.supabase_client.create_client")
    def test_init_connection_failure(self, mock_create_client):
        """Test initialization failure when connection test fails"""
        from src.utils.supabase_client import SupabaseClient

        # Setup mock to fail on test query
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception(
            "Connection failed"
        )
        mock_create_client.return_value = mock_client

        with pytest.raises(RuntimeError) as exc_info:
            SupabaseClient()

        assert "Supabase client creation or test query failed" in str(exc_info.value)

    @patch("src.utils.supabase_client.create_client")
    def test_get_lead_by_phone_success(self, mock_create_client):
        """Test successful lead retrieval by phone"""
        from src.utils.supabase_client import SupabaseClient

        # Setup mocks
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [{"phone": "+1234567890", "name": "John Doe"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Mock the test query
        test_response = Mock()
        test_response.data = []
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            test_response
        )

        mock_create_client.return_value = mock_client

        client = SupabaseClient()
        result = client.get_lead_by_phone("+1234567890")

        assert result == {"phone": "+1234567890", "name": "John Doe"}

    @patch("src.utils.supabase_client.create_client")
    def test_get_lead_by_phone_not_found(self, mock_create_client):
        """Test lead retrieval when not found"""
        from src.utils.supabase_client import SupabaseClient

        # Setup mocks
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Mock the test query
        test_response = Mock()
        test_response.data = []
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            test_response
        )

        mock_create_client.return_value = mock_client

        client = SupabaseClient()
        result = client.get_lead_by_phone("+1234567890")

        assert result is None

    @patch("src.utils.supabase_client.create_client")
    def test_create_lead_success(self, mock_create_client):
        """Test successful lead creation"""
        from src.utils.supabase_client import SupabaseClient

        # Setup mocks
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [{"phone": "+1234567890", "name": "John Doe"}]
        mock_client.table.return_value.insert.return_value.execute.return_value = (
            mock_response
        )

        # Mock the test query
        test_response = Mock()
        test_response.data = []
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            test_response
        )

        mock_create_client.return_value = mock_client

        client = SupabaseClient()
        result = client.create_lead("+1234567890", "John Doe", "Hello")

        assert result == {"phone": "+1234567890", "name": "John Doe"}

    @patch("src.utils.supabase_client.create_client")
    def test_get_missing_fields(self, mock_create_client):
        """Test getting missing required fields"""
        from src.utils.supabase_client import SupabaseClient

        # Setup mocks
        mock_client = Mock()
        test_response = Mock()
        test_response.data = []
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            test_response
        )
        mock_create_client.return_value = mock_client

        client = SupabaseClient()

        lead = {
            "move_in_date": "2024-01-01",
            "price": "",
            "beds": "2",
            "baths": None,
            "location": "Boston",
            "amenities": "",
        }

        missing = client.get_missing_fields(lead)

        # Should find price, baths, and amenities as missing
        assert "price" in missing
        assert "baths" in missing
        assert "amenities" in missing
        assert "move_in_date" not in missing
        assert "beds" not in missing
        assert "location" not in missing

    @patch("src.utils.supabase_client.create_client")
    def test_get_missing_optional_fields(self, mock_create_client):
        """Test getting missing optional fields"""
        from src.utils.supabase_client import SupabaseClient

        # Setup mocks
        mock_client = Mock()
        test_response = Mock()
        test_response.data = []
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            test_response
        )
        mock_create_client.return_value = mock_client

        client = SupabaseClient()

        lead = {"rental_urgency": "high", "boston_rental_experience": ""}

        missing = client.get_missing_optional_fields(lead)

        # Should find boston_rental_experience as missing
        assert "boston_rental_experience" in missing
        assert "rental_urgency" not in missing

    @patch("src.utils.supabase_client.create_client")
    def test_is_qualification_complete(self, mock_create_client):
        """Test qualification completion check"""
        from src.utils.supabase_client import SupabaseClient

        # Setup mocks
        mock_client = Mock()
        test_response = Mock()
        test_response.data = []
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            test_response
        )
        mock_create_client.return_value = mock_client

        client = SupabaseClient()

        complete_lead = {
            "move_in_date": "2024-01-01",
            "price": "$2000",
            "beds": "2",
            "baths": "1",
            "location": "Boston",
            "amenities": "parking",
        }

        incomplete_lead = {
            "move_in_date": "2024-01-01",
            "price": "",
            "beds": "2",
            "baths": "1",
            "location": "Boston",
            "amenities": "parking",
        }

        assert client.is_qualification_complete(complete_lead) is True
        assert client.is_qualification_complete(incomplete_lead) is False

    @patch("src.utils.supabase_client.create_client")
    def test_needs_tour_availability(self, mock_create_client):
        """Test tour availability need check"""
        from src.utils.supabase_client import SupabaseClient

        # Setup mocks
        mock_client = Mock()
        test_response = Mock()
        test_response.data = []
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            test_response
        )
        mock_create_client.return_value = mock_client

        client = SupabaseClient()

        qualified_no_tour = {
            "move_in_date": "2024-01-01",
            "price": "$2000",
            "beds": "2",
            "baths": "1",
            "location": "Boston",
            "amenities": "parking",
            "tour_availability": "",
            "tour_ready": False,
        }

        qualified_with_tour = {
            "move_in_date": "2024-01-01",
            "price": "$2000",
            "beds": "2",
            "baths": "1",
            "location": "Boston",
            "amenities": "parking",
            "tour_availability": "weekends",
            "tour_ready": False,
        }

        assert client.needs_tour_availability(qualified_no_tour) is True
        assert client.needs_tour_availability(qualified_with_tour) is False

    @patch("src.utils.supabase_client.create_client")
    def test_set_tour_ready(self, mock_create_client):
        """Test setting tour ready status"""
        from src.utils.supabase_client import SupabaseClient

        # Setup mocks
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [{"phone": "+1234567890", "tour_ready": True}]
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Mock the test query
        test_response = Mock()
        test_response.data = []
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            test_response
        )

        mock_create_client.return_value = mock_client

        client = SupabaseClient()
        result = client.set_tour_ready("+1234567890")

        assert result is True

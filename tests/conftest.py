# Test configuration and fixtures
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def mock_env_vars():
    """Fixture to set up environment variables for testing"""
    env_vars = {
        "TELNYX_API_KEY": "test_telnyx_key",
        "TELNYX_PHONE_NUMBER": "+1234567890",
        "OPENAI_API_KEY": "test_openai_key",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test_supabase_key",
        "AGENT_PHONE_NUMBER": "+1987654321",
        "OPENAI_MODEL": "gpt-4o-mini",
        "MOCK_TELNX": "1",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing"""
    return {
        "phone": "+1234567890",
        "name": "John Doe",
        "email": "john@example.com",
        "move_in_date": "2024-01-01",
        "price": "$2000-2500",
        "beds": "2",
        "baths": "1",
        "location": "Boston",
        "amenities": "parking, gym",
        "tour_availability": "",
        "tour_ready": False,
        "chat_history": "2024-01-01 10:00 - Lead: Hi, looking for apartments\n",
        "follow_up_count": 0,
        "next_follow_up_time": None,
        "follow_up_paused_until": None,
        "follow_up_stage": "first",
        "rental_urgency": "",
        "boston_rental_experience": "",
    }


@pytest.fixture
def sample_webhook_event():
    """Sample Telnyx webhook event for testing"""
    return {
        "body": '{"data": {"event_type": "message.received", "payload": {"from": {"phone_number": "+1234567890"}, "to": [{"phone_number": "+1987654321"}], "text": "Hi, I\'m looking for a 2 bedroom apartment"}}}'
    }


@pytest.fixture
def sample_outreach_event():
    """Sample outreach event for testing"""
    return {"phone_number": "+1234567890", "name": "Jane Smith"}

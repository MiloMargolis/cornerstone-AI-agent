"""
Shared test fixtures and configuration for the test suite.
"""
import pytest
import os
from unittest.mock import Mock, AsyncMock


@pytest.fixture(autouse=True)
def mock_environment_variables():
    """Mock environment variables for all tests"""
    env_vars = {
        'OPENAI_API_KEY': 'test-openai-key',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-supabase-key',
        'AGENT_PHONE_NUMBER': '+1987654321',
        'MOCK_TELNX': '1'
    }
    
    with pytest.MonkeyPatch().context() as m:
        for key, value in env_vars.items():
            m.setenv(key, value)
        yield


@pytest.fixture
def mock_lead():
    """Create a mock lead for testing"""
    from src.models.lead import Lead
    
    return Lead(
        phone="+1234567890",
        name="John Doe",
        email="john@example.com",
        beds="2",
        baths="1",
        move_in_date="2024-02-01",
        price="2000",
        location="Boston",
        amenities="Parking",
        tour_availability="Tuesday 2pm",
        tour_ready=False,
        follow_up_count=1,
        follow_up_stage="second"
    )


@pytest.fixture
def mock_webhook_event():
    """Create a mock webhook event for testing"""
    from src.models.webhook import WebhookEvent, MessagePayload, EventType
    
    payload = MessagePayload(
        from_number="+1234567890",
        to_numbers=["+1987654321"],
        text="Hello there",
        message_id="msg-123",
        timestamp="2024-01-01T10:00:00Z"
    )
    
    return WebhookEvent(
        event_type=EventType.MESSAGE_RECEIVED,
        payload=payload,
        event_id="test-event-123",
        timestamp="2024-01-01T10:00:00Z"
    )


@pytest.fixture
def mock_lead_repository():
    """Create a mock lead repository for testing"""
    mock_repo = Mock()
    
    # Make async methods return values
    mock_repo.get_by_phone = AsyncMock()
    mock_repo.create = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.add_message_to_history = AsyncMock()
    mock_repo.pause_follow_up_until = AsyncMock()
    mock_repo.set_tour_ready = AsyncMock()
    mock_repo.get_missing_fields = AsyncMock()
    mock_repo.get_missing_optional_fields = AsyncMock()
    mock_repo.needs_tour_availability = AsyncMock()
    mock_repo.schedule_follow_up = AsyncMock()
    mock_repo.get_leads_needing_follow_up = AsyncMock()
    
    return mock_repo


@pytest.fixture
def mock_messaging_service():
    """Create a mock messaging service for testing"""
    mock_service = Mock()
    
    # Make async methods return values
    mock_service.send_sms = AsyncMock()
    mock_service.send_agent_notification = AsyncMock()
    
    return mock_service


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service for testing"""
    mock_service = Mock()
    
    # Make async methods return values
    mock_service.extract_lead_info = AsyncMock()
    mock_service.generate_response = AsyncMock()
    mock_service.generate_delay_response = AsyncMock()
    
    return mock_service


@pytest.fixture
def mock_delay_detection_service():
    """Create a mock delay detection service for testing"""
    mock_service = Mock()
    
    # Make async methods return values
    mock_service.detect_delay_request = AsyncMock()
    mock_service.calculate_delay_until = AsyncMock()
    
    return mock_service


@pytest.fixture
def mock_error_handler():
    """Create a mock error handler for testing"""
    mock_handler = Mock()
    
    mock_handler.handle_validation_error.return_value = {
        "statusCode": 400,
        "body": '{"error": "Validation Error"}'
    }
    
    mock_handler.handle_internal_error.return_value = {
        "statusCode": 500,
        "body": '{"error": "Internal Error"}'
    }
    
    return mock_handler

# Test Suite Documentation

This directory contains comprehensive test coverage for the Cornerstone AI Agent application.

## Test Structure

The test suite is organized by module to match the source code structure:

### Core Tests (`test_core/`)
- **`test_webhook_handler.py`** - Tests for webhook processing
  - Service registration and resolution
  - Singleton vs regular service registration
  - Service building and configuration
  - Environment-based service selection

- **`test_lead_processor.py`** - Tests for core lead processing logic
  - New lead message processing
  - Existing lead message processing
  - Delay request handling
  - Tour-ready lead handling
  - Tour availability completion
  - Error handling and fallbacks
  - Follow-up scheduling

- **`test_event_processor.py`** - Tests for webhook event processing
  - Event validation
  - Phone number validation
  - Event processing success/failure
  - Error handling

### Handler Tests (`test_handlers/`)
- **`test_webhook_handler.py`** - Tests for webhook Lambda handler
  - Successful webhook processing
  - Event validation failures
  - Ignored event types
  - Agent message filtering
  - JSON parsing errors
  - Processing errors

- **`test_follow_up_handler.py`** - Tests for follow-up Lambda handler
  - Follow-up processing for multiple leads
  - No leads needing follow-up
  - Follow-up failures
  - Individual follow-up processing
  - Maximum follow-up limits

- **`test_outreach_handler.py`** - Tests for outreach Lambda handler
  - Initial outreach message sending
  - Input validation
  - Phone number validation
  - Lead creation
  - SMS sending
  - Error handling

### Middleware Tests (`test_middleware/`)
- **`test_error_handler.py`** - Tests for error handling middleware
  - Validation errors (400)
  - Authentication errors (401)
  - Authorization errors (403)
  - Not found errors (404)
  - Internal server errors (500)
  - Service unavailable errors (503)
  - Rate limit errors (429)
  - Database errors
  - External API errors
  - Webhook processing errors
  - Logging functionality

### Model Tests (`test_models/`)
- **`test_lead.py`** - Tests for Lead data model
  - Lead creation and validation
  - Required field validation
  - Lead qualification logic
  - Missing fields detection
  - Tour availability logic
  - Data serialization/deserialization
  - Lead status management

- **`test_webhook.py`** - Tests for WebhookEvent data model
  - Webhook event creation from Telnyx data
  - Event validation
  - Message payload handling
  - Event type filtering
  - Agent message detection
  - Data serialization

### Service Tests (`test_services/`)
- **`test_ai_service.py`** - Tests for OpenAI service
  - Lead information extraction
  - Response generation
  - Phase-based instructions
  - Delay response generation
  - Error handling
  - OpenAI API integration

- **`test_lead_repository.py`** - Tests for database operations
  - Lead CRUD operations
  - Message history management
  - Follow-up scheduling
  - Tour ready status management
  - Missing fields detection
  - Supabase integration

## Test Configuration

### Shared Fixtures (`conftest.py`)
The test suite includes shared fixtures for:
- Environment variable mocking
- Mock lead data
- Mock webhook events
- Mock services (repository, messaging, AI, delay detection)
- Mock error handler

### Test Dependencies
Tests use the following key dependencies:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `unittest.mock` - Mocking and patching

## Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Tests by Module
```bash
# Core tests
python -m pytest tests/test_core/ -v

# Handler tests
python -m pytest tests/test_handlers/ -v

# Middleware tests
python -m pytest tests/test_middleware/ -v

# Model tests
python -m pytest tests/test_models/ -v

# Service tests
python -m pytest tests/test_services/ -v
```

### Run Tests with Coverage
```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

### Run Specific Test Files
```bash
python -m pytest tests/test_core/test_lead_processor.py -v
```

### Run Specific Test Methods
```bash
python -m pytest tests/test_core/test_lead_processor.py::TestLeadProcessor::test_process_new_lead_message -v
```

## Test Coverage

The test suite provides comprehensive coverage for:

### Core Business Logic
- Lead message processing workflows
- Event validation and processing
- Simplified service management and direct instantiation

### API Handlers
- Lambda function entry points
- Input validation and error handling
- Response formatting

### Data Models
- Data validation and business rules
- Serialization/deserialization
- State management

### External Integrations
- Database operations (Supabase)
- AI service integration (OpenAI)
- Messaging service integration (Telnyx)

### Error Handling
- Validation errors
- Authentication/authorization errors
- Service failures
- Network errors

## Test Patterns

### Async Testing
All async functions are tested using `pytest-asyncio` with proper async/await patterns.

### Mocking Strategy
- External services are mocked to avoid network calls
- Database operations are mocked to avoid test data persistence
- Environment variables are mocked for consistent test environment

### Error Scenarios
Each test module includes comprehensive error scenario testing:
- Missing required data
- Invalid input formats
- Service failures
- Network timeouts
- Database errors

### Edge Cases
Tests cover edge cases such as:
- Empty or null values
- Boundary conditions
- Race conditions
- Resource exhaustion

## Best Practices

1. **Isolation**: Each test is independent and doesn't rely on other tests
2. **Descriptive Names**: Test methods have clear, descriptive names
3. **Arrange-Act-Assert**: Tests follow the AAA pattern
4. **Mocking**: External dependencies are properly mocked
5. **Error Testing**: Both success and failure scenarios are tested
6. **Async Support**: All async functions are properly tested
7. **Coverage**: High test coverage for critical business logic

## Maintenance

When adding new features:
1. Add corresponding tests in the appropriate module
2. Update shared fixtures if needed
3. Ensure new tests follow existing patterns
4. Run the full test suite to verify no regressions
5. Update this documentation if test structure changes

# CornerStone AI SMS Assistant

A sophisticated AI-powered SMS follow-up assistant for real estate lead qualification and management, built with AWS Lambda and modern architectural patterns.

## 🎯 Overview

CornerStone AI SMS Assistant is a serverless application that automates real estate lead qualification through natural SMS conversations. It uses OpenAI's GPT-4 to intelligently extract lead information, manage follow-up sequences, and coordinate with human agents when leads are ready for property tours.

### Key Features
- **Intelligent Lead Qualification**: AI extracts and tracks lead preferences (bedrooms, bathrooms, price, location, move-in date, amenities)
- **Natural SMS Conversations**: Human-like responses that adapt to conversation context
- **Automated Follow-ups**: Scheduled follow-up messages with intelligent timing
- **Tour Readiness Detection**: Automatically notifies agents when leads are ready for tours
- **Multi-Phase Qualification**: Progressive information gathering with optional field collection
- **Delay Request Handling**: Respects lead requests to pause follow-ups
- **Manual Outreach**: API endpoint for initiating conversations with new leads

## 🏗️ Architecture

This application follows **Clean Architecture** principles with clear separation of concerns, event-driven design, and enterprise-level patterns for scalability and maintainability.

### Core Technologies
- **AWS Lambda** - Serverless compute platform
- **Python 3.11** - Primary programming language
- **AWS SAM** - Infrastructure as Code deployment
- **OpenAI GPT-4** - Conversational AI and lead qualification
- **Telnyx API** - SMS messaging platform
- **Supabase** - PostgreSQL database with real-time features
- **Google Sheets API** - Data export and reporting

### Architectural Patterns
- **Event-Driven Architecture** - Asynchronous message processing
- **Service Layer Pattern** - Business logic abstraction
- **Repository Pattern** - Data access abstraction
- **Domain-Driven Design** - Rich domain models with business logic
- **Interface Segregation** - Clean service contracts

## 📁 Project Structure

```
src/
├── handlers/              # 🚀 Lambda Entry Points
│   ├── webhook_handler.py      # Telnyx webhook processor
│   ├── follow_up_handler.py    # Scheduled follow-up processor
│   └── outreach_handler.py     # Manual outreach API
├── core/                  # 🧠 Business Logic
│   ├── event_processor.py      # Event processing logic
│   └── lead_processor.py       # Core lead qualification logic
├── models/                # 📊 Domain Models
│   ├── lead.py                 # Lead domain model
│   └── webhook.py              # Webhook event model
├── services/              # 🔌 External Integrations
│   ├── interfaces.py           # Service contracts
│   ├── database/
│   │   └── lead_repository.py  # Data access layer
│   ├── messaging/
│   │   └── telnyx_service.py   # SMS messaging service
│   ├── ai/
│   │   └── openai_service.py   # AI/ML service
│   └── delay_detection/
│       └── delay_detection_service.py  # Delay detection logic
├── middleware/            # 🛡️ Cross-cutting Concerns
│   └── error_handler.py        # Centralized error handling
├── config/                # ⚙️ Configuration
│   └── follow_up_config.py     # Business rules and scheduling
├── utils/                 # 🛠️ Shared Utilities
│   ├── constants.py            # Application constants
│   ├── prompt_loader.py        # Template loading
│   ├── google_sheets_client.py # Data export
│   └── prompts/                # AI prompt templates
└── requirements.txt       # 📦 Dependencies
```

## 🚀 Lambda Functions

### WebhookHandlerFunction
- **Purpose**: Processes incoming Telnyx SMS webhooks
- **Trigger**: API Gateway POST `/webhook`
- **Handler**: `handlers.webhook_handler.lambda_handler`
- **Features**: 
  - Real-time message processing
  - Lead qualification and information extraction
  - Automated responses based on lead state
  - Agent notification when tour-ready

### FollowUpHandlerFunction
- **Purpose**: Processes scheduled follow-up messages
- **Trigger**: CloudWatch Events (every 30 minutes)
- **Handler**: `handlers.follow_up_handler.lambda_handler`
- **Features**:
  - Batch processing of leads needing follow-up
  - Intelligent scheduling based on lead state
  - Progressive follow-up messaging

### OutreachHandlerFunction
- **Purpose**: Manual outreach and lead management
- **Trigger**: API Gateway POST `/outreach`
- **Handler**: `handlers.outreach_handler.lambda_handler`
- **Features**:
  - Manual lead outreach capabilities
  - Lead creation and initial messaging
  - Phone number validation and normalization

## 🧠 Core Business Logic

### Lead Processing Workflow
1. **Message Reception** - Webhook receives SMS from Telnyx
2. **Lead Identification** - Find or create lead record
3. **Information Extraction** - AI extracts relevant data from message
4. **Lead Qualification** - Determine missing required/optional fields
5. **Response Generation** - AI generates contextual response
6. **State Management** - Update lead status and schedule follow-ups
7. **Agent Notification** - Notify human agent when tour-ready

### Lead Qualification Phases
- **QUALIFICATION** - Collect required fields (move-in date, price, beds, baths, location, amenities)
- **OPTIONAL_QUESTIONS** - Gather additional context (Boston rental experience)
- **TOUR_SCHEDULING** - Coordinate tour availability
- **COMPLETE** - Lead is fully qualified and tour-ready

### Required Fields
- `move_in_date` - When the lead wants to move in
- `price` - Budget/price range
- `beds` - Number of bedrooms needed
- `baths` - Number of bathrooms needed
- `location` - Preferred neighborhoods/areas
- `amenities` - Desired amenities (parking, laundry, etc.)

### Optional Fields
- `boston_rental_experience` - Previous rental experience in Boston

## 🔌 Service Layer

### AI Service (`OpenAIService`)
- **Purpose**: OpenAI integration for lead qualification and response generation
- **Features**:
  - Information extraction from natural language
  - Contextual response generation
  - Phase-based conversation management
  - Virtual lead state management

### Messaging Service (`TelnyxService`)
- **Purpose**: SMS communication via Telnyx
- **Features**:
  - Async SMS sending
  - Agent notifications
  - Mock service for testing
  - Error handling and retry logic

### Database Service (`LeadRepository`)
- **Purpose**: Data persistence and retrieval
- **Features**:
  - Lead CRUD operations
  - Message history management
  - Follow-up scheduling
  - Tour readiness tracking
  - Returns domain models, not raw data

### Delay Detection Service (`DelayDetectionService`)
- **Purpose**: Process delay requests from leads
- **Features**:
  - AI-powered delay detection
  - Intelligent scheduling
  - Follow-up pause management

## 📊 Domain Models

### Lead Model
```python
@dataclass
class Lead:
    phone: str
    name: str = ""
    email: str = ""
    beds: str = ""
    baths: str = ""
    move_in_date: str = ""
    price: str = ""
    location: str = ""
    amenities: str = ""
    tour_availability: str = ""
    tour_ready: bool = False
    chat_history: str = ""
    follow_up_count: int = 0
    next_follow_up_time: Optional[str] = None
    follow_up_paused_until: Optional[str] = None
    follow_up_stage: str = "scheduled"
    boston_rental_experience: str = ""
```

### Webhook Event Model
```python
@dataclass
class WebhookEvent:
    event_type: EventType
    payload: MessagePayload
    
    @classmethod
    def from_telnyx_webhook(cls, data: Dict[str, Any]) -> 'WebhookEvent':
        # Validates and creates event from raw webhook data
```

## 🛡️ Error Handling

### Centralized Error Handler
- **Validation Errors** - Invalid input data
- **Internal Errors** - Application logic failures
- **Authentication Errors** - API key issues
- **Not Found Errors** - Missing resources
- **Rate Limit Errors** - API throttling
- **Structured Responses** - Consistent error format

### Error Response Format
```json
{
  "statusCode": 400,
  "body": {
    "error": "validation_error",
    "message": "Invalid phone number format",
    "details": {}
  }
}
```

## 🔧 Configuration

### Environment Variables
```bash
# API Keys
TELNYX_API_KEY=your_telnyx_key
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Phone Numbers
TELNYX_PHONE_NUMBER=+1234567890
AGENT_PHONE_NUMBER=+1987654321

# AI Configuration
OPENAI_MODEL=gpt-4o-mini

# Testing
MOCK_TELNX=0  # Set to 1 for mock SMS service
```

### Business Rules (`config/follow_up_config.py`)
- Follow-up scheduling intervals
- Delay keyword detection
- Tour readiness criteria
- Message templates

## 🧪 Testing

### Service Testing
- Mock services for external dependencies
- Interface-based testing
- Async/await support
- Comprehensive error scenarios

### Integration Testing
- End-to-end webhook processing
- Database operations
- SMS sending workflows
- AI response generation

### Test Structure
```
tests/
├── test_core/
│   ├── test_event_processor.py
│   └── test_lead_processor.py
├── test_handlers/
│   ├── test_webhook_handler.py
│   ├── test_follow_up_handler.py
│   └── test_outreach_handler.py
├── test_services/
│   ├── test_ai_service.py
│   └── test_lead_repository.py
└── test_models/
    ├── test_lead.py
    └── test_webhook.py
```

## 🚀 Deployment

### Prerequisites
- AWS CLI configured
- AWS SAM CLI installed
- Python 3.11+
- Required API keys and credentials

### Deployment Steps
```bash
# 1. Install dependencies
pip install -r src/requirements.txt

# 2. Build SAM application
sam build

# 3. Deploy to AWS
sam deploy --guided

# 4. Configure webhook URL in Telnyx
# Use the WebhookUrl output from deployment
```

### SAM Template Features
- **Parameters**: Secure credential management
- **Globals**: Consistent function configuration
- **Resources**: Three Lambda functions with proper triggers
- **Outputs**: Useful endpoints and ARNs

## 📈 Monitoring & Observability

### CloudWatch Metrics
- Function invocation counts
- Error rates and durations
- Memory utilization
- Concurrent executions

### Logging
- Structured JSON logging
- Request/response tracking
- Error context preservation
- Performance metrics

### Alerts
- High error rates
- Function timeouts
- API quota limits
- Database connection issues

## 🔒 Security

### API Security
- Environment variable encryption
- IAM role-based access
- API Gateway authentication
- Request validation

### Data Protection
- PII handling best practices
- Database encryption at rest
- Secure credential management
- Audit logging

## 📚 API Reference

### Webhook Endpoint
```
POST /webhook
Content-Type: application/json

{
  "data": {
    "event_type": "message.received",
    "payload": {
      "from": {"phone_number": "+1234567890"},
      "to": [{"phone_number": "+1987654321"}],
      "text": "Hi, I'm looking for a 2 bedroom apartment"
    }
  }
}
```

### Outreach Endpoint
```
POST /outreach
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "name": "John Doe"
}
```


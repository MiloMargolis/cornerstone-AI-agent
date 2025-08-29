# CornerStone AI SMS Assistant - Setup Instructions

## 🎯 Overview

CornerStone AI SMS Assistant is a serverless application that automates real estate lead qualification through natural SMS conversations. This guide will walk you through setting up the complete system from scratch.

## 📋 Prerequisites

### Required Accounts & Services
1. **AWS Account** with appropriate permissions
2. **Telnyx Account** with SMS-enabled phone number
3. **Supabase Project** with PostgreSQL database
4. **OpenAI API Account** with GPT-4 access

### Development Tools
1. **AWS CLI** configured with appropriate permissions
2. **AWS SAM CLI** installed and configured
3. **Python 3.11** installed
4. **Git** for version control

## 🚀 Quick Start

### 1. Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd cornerstone-AI-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r src/requirements.txt
```

### 2. Environment Configuration

```bash
# Create environment file
cp .env.example .env
```

Fill in your `.env` file with actual values:

```bash
# API Keys
TELNYX_API_KEY=your_telnyx_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_service_role_secret_key_here

# Phone Numbers
TELNYX_PHONE_NUMBER=+1234567890
AGENT_PHONE_NUMBER=+1987654321

# AI Configuration
OPENAI_MODEL=gpt-4o-mini

# Testing (optional)
MOCK_TELNX=0
```

## 🗄️ Database Setup (Supabase)

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and service role key

### 2. Create Leads Table

Run this SQL in your Supabase SQL editor:

```sql
-- Create leads table
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid(),
    phone TEXT NOT NULL UNIQUE,
    name TEXT DEFAULT ''::text,
    email TEXT DEFAULT ''::text,
    beds TEXT DEFAULT ''::text,
    baths TEXT DEFAULT ''::text,
    move_in_date TEXT DEFAULT ''::text,
    price TEXT DEFAULT ''::text,
    location TEXT DEFAULT ''::text,
    amenities TEXT DEFAULT ''::text,
    tour_availability TEXT DEFAULT ''::text,
    tour_ready BOOLEAN DEFAULT FALSE,
    follow_up_count INTEGER DEFAULT 0,
    follow_up_stage TEXT DEFAULT 'scheduled',
    next_follow_up_time TIMESTAMP,
    follow_up_paused_until TIMESTAMP,
    boston_rental_experience TEXT DEFAULT ''::text,
    chat_history TEXT DEFAULT ''::text,
    last_contacted TIMESTAMP,
    date_connected TIMESTAMP DEFAULT now(),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX idx_leads_phone ON leads(phone);
CREATE INDEX idx_leads_tour_ready ON leads(tour_ready);
CREATE INDEX idx_leads_next_follow_up ON leads(next_follow_up_time);
CREATE INDEX idx_leads_last_contacted ON leads(last_contacted);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Create policy for full access (adjust as needed)
CREATE POLICY "Full access to leads" ON leads FOR ALL USING (true);
```

### 3. Verify Table Structure

Your table should have these columns:
- `id` (SERIAL, Primary Key)
- `uuid` (UUID, Default: gen_random_uuid())
- `phone` (TEXT, Unique)
- `name` (TEXT, Default: ''::text)
- `email` (TEXT, Default: ''::text)
- `beds` (TEXT, Default: ''::text)
- `baths` (TEXT, Default: ''::text)
- `move_in_date` (TEXT, Default: ''::text)
- `price` (TEXT, Default: ''::text)
- `location` (TEXT, Default: ''::text)
- `amenities` (TEXT, Default: ''::text)
- `tour_availability` (TEXT, Default: ''::text)
- `tour_ready` (BOOLEAN, Default: FALSE)
- `follow_up_count` (INTEGER, Default: 0)
- `follow_up_stage` (TEXT, Default: 'scheduled')
- `next_follow_up_time` (TIMESTAMP)
- `follow_up_paused_until` (TIMESTAMP)
- `boston_rental_experience` (TEXT, Default: ''::text)
- `chat_history` (TEXT, Default: ''::text)
- `last_contacted` (TIMESTAMP)
- `date_connected` (TIMESTAMP, Default: now())

## 📱 Telnyx Setup

### 1. Create Telnyx Account
1. Go to [telnyx.com](https://telnyx.com)
2. Sign up for an account
3. Add payment method

### 2. Get API Key
1. Navigate to **Portal → API Keys**
2. Create a new API key
3. Copy the key to your `.env` file

### 3. Purchase Phone Number
1. Go to **Portal → Phone Numbers**
2. Search for available numbers
3. Purchase a number with SMS capabilities
4. Copy the number to your `.env` file

### 4. Configure Messaging Profile
1. Go to **Portal → Messaging → Messaging Profiles**
2. Create a new messaging profile
3. Assign your phone number to the profile
4. **Important**: Don't configure webhook yet (we'll do this after deployment)

## 🤖 OpenAI Setup

### 1. Create OpenAI Account
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up for an account
3. Add payment method

### 2. Get API Key
1. Go to **API Keys** section
2. Create a new API key
3. Copy the key to your `.env` file

### 3. Verify Model Access
Ensure you have access to `gpt-4o-mini` or update the model in your configuration.

## 🧪 Local Development

### 1. Test Dependencies

```bash
# Test database connection
cd src
python -c "
from services.database.lead_repository import LeadRepository
import asyncio

async def test_db():
    repo = LeadRepository()
    print('Database connection successful!')

asyncio.run(test_db())
"

# Test OpenAI connection
python -c "
from services.ai.openai_service import OpenAIService
import asyncio

async def test_openai():
    ai = OpenAIService()
    print('OpenAI connection successful!')

asyncio.run(test_openai())
"
```

### 2. Run Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_handlers/ -v
python -m pytest tests/test_services/ -v
python -m pytest tests/test_core/ -v
```

### 3. Local Testing

```bash
# Test webhook handler locally
cd src
python handlers/webhook_handler.py

# Test follow-up handler locally
python handlers/follow_up_handler.py

# Test outreach handler locally
python handlers/outreach_handler.py
```

## ☁️ AWS Deployment

### 1. AWS CLI Configuration

```bash
# Configure AWS CLI
aws configure

# Verify configuration
aws sts get-caller-identity
```

### 2. SAM CLI Setup

```bash
# Verify SAM CLI installation
sam --version

# Build the application
sam build

# Deploy (first time - guided)
sam deploy --guided
```

During guided deployment, you'll be prompted for:
- **Stack name**: `cornerstone-ai-sms` (or your preferred name)
- **AWS region**: Choose your preferred region
- **Parameter values**: Enter your API keys and configuration

### 3. Deployment Parameters

You'll need to provide these parameters during deployment:

```
Parameter Name                    | Value
----------------------------------|----------------------------------
TelnyxApiKey                      | your_telnyx_api_key
TelnyxPhoneNumber                 | +1234567890
OpenAIApiKey                      | your_openai_api_key
SupabaseUrl                       | https://your-project.supabase.co
SupabaseKey                       | your_supabase_service_role_key
AgentPhoneNumber                  | +1987654321
```

### 4. Post-Deployment

After successful deployment, note the outputs:

```bash
# Get deployment outputs
sam list outputs

# Look for the WebhookUrl output
# It will look like: https://abcdef123.execute-api.us-east-1.amazonaws.com/Prod/webhook
```

## 🔗 Telnyx Webhook Configuration

### 1. Configure Webhook URL
1. Go to **Portal → Messaging → Messaging Profiles**
2. Edit your messaging profile
3. Set **Webhook URL** to the API Gateway URL from deployment
4. Set **HTTP method** to `POST`
5. Enable webhook for `message.received` events
6. Save the configuration

### 2. Test Webhook
1. Send a test SMS to your Telnyx number
2. Check CloudWatch logs for webhook processing
3. Verify the message appears in your Supabase database

## 🧪 Testing the Complete System

### 1. Create Test Group Chat
Create a group chat with:
- Lead's phone number
- Agent's phone number (from your .env)
- AI assistant's phone number (your Telnyx number)

### 2. Send Test Messages

**Test 1: Basic Qualification**
```
Lead: Hi, I'm looking for a 2 bedroom apartment
```

**Test 2: Information Extraction**
```
Lead: I need something around $2000/month, preferably in Cambridge, move-in September 1st
```

**Test 3: Tour Availability**
```
Lead: I'm available weekends and evenings for tours
```

### 3. Monitor System

```bash
# Check CloudWatch logs
sam logs -n WebhookHandlerFunction --stack-name cornerstone-ai-sms --tail

# Check follow-up processing
sam logs -n FollowUpHandlerFunction --stack-name cornerstone-ai-sms --tail

# Check Supabase dashboard for lead data
```

## 🔧 Configuration Options

### Follow-up Schedule
Edit `src/config/follow_up_config.py` to customize:

```python
FOLLOW_UP_SCHEDULE = [
    {"days": 1, "stage": "first"},
    {"days": 3, "stage": "second"},
    {"days": 5, "stage": "third"},
    {"days": 7, "stage": "fourth"},
    {"days": 10, "stage": "final"},
]

MAX_FOLLOW_UPS = 5
```

### AI Prompts
Customize AI behavior by editing templates in `src/utils/prompts/`:
- `extraction.tmpl` - Information extraction logic
- `qualification_system.tmpl` - Response generation logic

### Business Rules
Modify `src/utils/constants.py` to adjust:
- Required fields for qualification
- Optional fields
- Phase configurations
# CornerStone AI SMS Assistant - Setup Instructions

## Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **AWS SAM CLI** installed
3. **Python 3.11** installed
4. **Telnyx account** with SMS-enabled phone number
5. **Supabase project** with the `leads` table created
6. **OpenAI API key**

## Environment Setup

1. **Clone and navigate to project:**
   ```bash
   cd cornerstone-AI-agent
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Fill in your .env file with actual values:**
   ```
   TELNYX_API_KEY=your_telnyx_api_key_here
   TELNYX_PHONE_NUMBER=your_telnyx_phone_number_here
   OPENAI_API_KEY=your_openai_api_key_here
   SUPABASE_URL=your_supabase_project_url_here
   SUPABASE_KEY=your_supabase_service_role_secret_key_here
   AGENT_PHONE_NUMBER=your_agent_phone_number_here
   ```

## Supabase Setup

Your `leads` table should already be created. Verify it has these columns:
- `id` (SERIAL, Primary Key)
- `uuid` (UUID, Default: gen_random_uuid())
- `phone` (TEXT)
- `text` (TEXT, Default: ''::text)
- `name` (TEXT, Default: ''::text)
- `email` (TEXT, Default: ''::text)
- `beds` (TEXT, Default: ''::text)
- `baths` (TEXT, Default: ''::text)
- `move_in_date` (TEXT, Default: ''::text)
- `price` (TEXT, Default: ''::text)
- `location` (TEXT, Default: ''::text)
- `amenities` (TEXT, Default: ''::text)
- `other_notes` (TEXT, Default: ''::text)
- `date_connected` (TIMESTAMP, Default: now())
- `last_contacted` (TIMESTAMP)

## Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test locally:**
   ```bash
   cd src
   python app.py
   ```

## AWS Deployment

1. **Build the application:**
   ```bash
   sam build
   ```

2. **Deploy (first time):**
   ```bash
   sam deploy --guided
   ```
   
   You'll be prompted to enter:
   - Stack name (e.g., `cornerstone-sms-assistant`)
   - AWS region
   - Your API keys and configuration values

3. **Deploy updates:**
   ```bash
   sam deploy
   ```

4. **Get the webhook URL:**
   After deployment, note the `WebhookUrl` output. It will look like:
   ```
   https://abcdef123.execute-api.us-east-1.amazonaws.com/Prod/webhook
   ```

## Telnyx Configuration

1. **Log into your Telnyx account**
2. **Navigate to Messaging → Messaging Profiles**
3. **Create or edit your messaging profile**
4. **Set the webhook URL** to the API Gateway URL from the deployment output
5. **Set HTTP method** to POST
6. **Enable webhook** for `message.received` events

## Testing

1. **Create a group chat** with:
   - Lead's phone number
   - Agent's phone number (from your .env)
   - AI assistant's phone number (your Telnyx number)

2. **Send a test message** from the lead's phone:
   ```
   Hi, I'm looking for a 2 bedroom apartment
   ```

3. **Check the logs:**
   ```bash
   sam logs -n SMSHandlerFunction --stack-name cornerstone-sms-assistant --tail
   ```

## Monitoring

- **CloudWatch Logs**: Check AWS CloudWatch for detailed logs
- **Supabase Dashboard**: Monitor lead data in your Supabase project
- **Telnyx Logs**: Check Telnyx dashboard for SMS delivery status

## Common Issues

1. **"Missing environment variable" errors:**
   - Verify all required environment variables are set in AWS Lambda
   - Check that the SAM template parameters match your actual values

2. **SMS not being sent:**
   - Verify Telnyx API key and phone number
   - Check Telnyx webhook is properly configured
   - Ensure phone numbers are in E.164 format (+1234567890)

3. **Database connection issues:**
   - Verify Supabase URL and key
   - Check that the `leads` table exists with correct schema

4. **OpenAI API errors:**
   - Verify OpenAI API key is valid
   - Check you have sufficient credits

## Next Steps

Once the MVP is working:
1. Add message history tracking
2. Implement follow-up cadence
3. Add Google Sheets integration
4. Customize AI personality and responses
5. Add MLS integration 
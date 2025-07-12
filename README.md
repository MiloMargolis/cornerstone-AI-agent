# ConerStone AI SMS Follow-Up Assistant

This is a serverless, AI-powered SMS assistant for real estate agents. It helps you automatically qualify and follow up with leads over SMS until they're ready to schedule a tour.

Built using:
- AWS Lambda (deployed with AWS SAM)
- Telnyx (for SMS messaging)
- Supabase (for lead tracking)
- OpenAI (for assistant responses)
- Google Sheets (for logging and visibility)

## Features

- Group SMS threads with leads and your AI assistant
- Customizable follow-up cadence
- Dynamic response generation using OpenAI
- Lead qualification (price range, move-in date, beds/baths, etc.)
- Writes all responses and lead info to Supabase and Google Sheets
- MLS data integration (planned)

## How It Works

When a new lead comes in, the agent creates a group text that includes:
- The lead
- The agent
- The AI assistant (using the Telnyx number)

The assistant introduces itself and begins asking questions to qualify the lead. These include:
- Move-in date
- Price range
- Number of bedrooms/bathrooms
- Preferred locations
- Desired amenities

The assistant continues the conversation until the lead is qualified or stops responding. It follows up automatically at set intervals and notifies the agent when it's time to take action (e.g., book a tour). All relevant lead data is written to Supabase and synced to Google Sheets in real time.

The backend is entirely serverless and runs on AWS Lambda, triggered by Telnyx webhooks. Responses are generated using OpenAI and stored with Supabase. Google Sheets is used as a lightweight CRM for visibility and logging.

This project is designed to replace the most repetitive and time-consuming part of the leasing workflow — chasing and qualifying leads — while keeping the agent in control and in the loop.


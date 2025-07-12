# DIRECTIONS.md

This document outlines how to implement the MVP version of the CornerStone AI SMS Follow-Up Assistant. The goal is to start simple: build a conversational assistant that integrates with OpenAI and Supabase, tracks lead conversations, and fills in qualifying data fields through natural conversation.

## MVP Objective

Build a Telnyx-connected AI assistant that:
- Participates in a group SMS chat with a lead
- Uses OpenAI to generate conversational replies
- Checks Supabase to "remember" what it already knows about the lead
- Asks only the questions it still needs to fill in the fields in the database
- Stores new messages and answers back to Supabase
- Identifies which lead it's talking to by the lead's phone number

This first version will not include:
- MLS integration
- Supabase sync with Google Sheets
- Follow-up cadence logic
Those will be added later as we iterate.

---

## Required Stack 
(assume I have API keys and just direct me on the structure of the .env)

- **AWS Lambda** (via AWS SAM)
- **Telnyx** for receiving/sending SMS
- **Supabase** as the database (Postgres)
- **OpenAI** for generating assistant responses

---

## Data Model (Supabase Table)

Table name: `leads`

This table stores one row per lead (based on phone number). It holds both the message history and the qualification fields.

| Column           | Type      | Default                     | Notes                                |
|------------------|-----------|------------------------------|--------------------------------------|
| `id`             | SERIAL    |                              | Auto-incremented primary key         |
| `uuid`           | UUID      | `gen_random_uuid()`          |                                      |
| `phone`          | TEXT      |                              | Lead’s phone number (identifier)     |
| `text`           | TEXT      | `''::text`                   | Most recent message or notes         |
| `name`           | TEXT      | `''::text`                   | Optional                              |
| `email`          | TEXT      | `''::text`                   | Optional                              |
| `beds`           | TEXT      | `''::text`                   | Optional                              |
| `baths`          | TEXT      | `''::text`                   | Optional                              |
| `move_in_date`   | TEXT      | `''::text`                   | Optional                              |
| `price`          | TEXT      | `''::text`                   | Optional                              |
| `location`       | TEXT      | `''::text`                   | Optional                              |
| `amenities`      | TEXT      | `''::text`                   | Optional                              |
| `other_notes`    | TEXT      | `''::text`                   | Optional                              |
| `date_connected` | TIMESTAMP | `now()`                      | When lead first contacted             |
| `last_contacted` | TIMESTAMP |                              | Last time AI messaged the lead       |

---

## MVP Behavior

1. **Incoming Message from Telnyx**
   - Webhook receives a POST from Telnyx with message data
   - Extract the phone number of the lead from the message metadata

2. **Identify the Lead**
   - Check Supabase for an existing row with that phone number
   - If no record exists, create one with default values

3. **Determine What’s Missing**
   - Look at the row for any empty fields (name, move_in_date, price, beds, baths, etc.)
   - Maintain a fixed question order for now

4. **Generate a Response**
   - Use OpenAI to continue the conversation naturally
   - If a qualifying field is still blank, prompt for it in a friendly way

5. **Store and Respond**
   - Save the message (incoming + outgoing) to Supabase
   - Send the generated reply back through Telnyx to the group thread

---

## Notes

- Each conversation is linked to a phone number, which uniquely identifies the lead, even within a group chat.
- The assistant only stops prompting when all fields are filled in.
- At this stage, chat history is tracked solely through Supabase: the assistant “remembers” what has or hasn’t been filled by checking the database fields.

---

## Next Steps (after MVP)

Once this flow is stable and understandable:
- Add follow-up timers and reminders based on `last_contacted`
- Introduce Google Sheets sync for visibility
- Customize tone and pacing per agent
- Use MLS API to recommend listings based on preferences
- Add admin dashboard for managing active leads and conversation history

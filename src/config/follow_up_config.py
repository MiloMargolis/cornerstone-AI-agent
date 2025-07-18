# Follow-up Configuration
FOLLOW_UP_SCHEDULE = [
    {"days": 1, "stage": "first"},
    {"days": 3, "stage": "second"}, 
    {"days": 5, "stage": "third"},
    {"days": 7, "stage": "fourth"},
    {"days": 10, "stage": "final"}
]

MAX_FOLLOW_UPS = 5

# Follow-up message templates (gentle reminders)
FOLLOW_UP_MESSAGES = {
    "first": "Hi! Just wanted to check in - are you still looking for an apartment? I'm here if you have any questions! 🏠",
    "second": "Hope you're doing well! I wanted to follow up on your apartment search. Let me know if you'd like to continue where we left off.",
    "third": "Hi there! Still thinking about your apartment search? I have all our previous conversation saved if you'd like to pick up where we left off.",
    "fourth": "Just checking in one more time - are you still interested in finding an apartment? I'm here to help whenever you're ready!",
    "final": "This will be my last check-in - if you're still looking for an apartment, just send me a message and I'll be happy to help! 😊"
}

# Keywords that indicate delay requests
DELAY_KEYWORDS = [
    # Time periods
    "give me", "call me", "contact me", "reach out", "check back", "follow up",
    # Time indicators
    "days", "weeks", "months", "week", "month", "day",
    # Specific times
    "next week", "next month", "in a week", "in a month", "few days", "few weeks",
    # Numbers with time
    "1 week", "2 weeks", "3 weeks", "1 month", "2 months",
    # Not ready indicators
    "not ready", "too early", "not yet", "later", "busy", "wait"
] 
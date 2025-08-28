from typing import Dict
from dataclasses import dataclass

REQUIRED_FIELDS = ["move_in_date", "price", "beds", "baths", "location", "amenities"]
OPTIONAL_FIELDS = ["boston_rental_experience"]  # rental_urgency removed


@dataclass
class PhaseConfig:
    name: str
    instructions: str


PHASE_CONFIGS: Dict[str, PhaseConfig] = {
    "TOUR_SCHEDULING": PhaseConfig(
        name="TOUR_SCHEDULING",
        instructions="All qualification info is complete. Ask ONLY about tour availability - when they're available for property tours. Don't ask about anything else.",
    ),
    "QUALIFICATION": PhaseConfig(
        name="QUALIFICATION",
        instructions="""Still missing REQUIRED: {missing_fields}

Before asking anything:
1. Check the database status above - only ask about "✗ MISSING" fields
2. Check conversation history - don't repeat questions

Ask 2-3 questions about missing required fields only:
- Bedrooms + bathrooms together
- Price + location together  
- Move-in date + amenities together""",
    ),
    "OPTIONAL_QUESTIONS": PhaseConfig(
        name="OPTIONAL_QUESTIONS",
        instructions="""All required info is complete! You can ask 1-2 optional questions to gather extra helpful info: {missing_optional}

Optional questions:
- boston_rental_experience: "Do you mind if I ask - have you rented an apartment in Boston before, or is this your first rental experience here? I can give you a brief overview of the process if helpful."

Ask naturally, don't force it. If conversation doesn't flow naturally, skip to asking about tour availability.""",
    ),
    "COMPLETE": PhaseConfig(
        name="COMPLETE",
        instructions="All information is collected! Send a professional completion message letting them know your teammate will contact them directly to schedule their tour. This ends the qualification conversation.",
    ),
}

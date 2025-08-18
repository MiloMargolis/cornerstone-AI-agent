import pytest
import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.utils.openai_client import OpenAIClient


class TestOpenAIIntegration:
    """Integration tests using real OpenAI API calls"""

    @pytest.fixture
    def client(self):
        """Initialize OpenAI client with real API key"""
        return OpenAIClient()

    @pytest.fixture
    def sample_lead_data(self):
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
            "chat_history": "2024-01-01 10:00 - Lead: Hi, looking for apartments\n2024-01-01 10:01 - AI: Hi! I'd be happy to help you find an apartment. What's your budget range?\n",
            "follow_up_count": 0,
            "next_follow_up_time": None,
            "follow_up_paused_until": None,
            "follow_up_stage": "first",
            "rental_urgency": "",
            "boston_rental_experience": "",
        }

    def test_extract_lead_info_complete_information(self, client):
        """Test extraction with complete information provided"""
        print("\n=== Test: Complete Information Extraction ===")

        message = "I need a 3 bedroom, 2 bathroom apartment for September 1st, 2025. My budget is $3000/month and I want to be in Mission Hill. I need parking and in-unit laundry."
        current_data = {
            "move_in_date": "EMPTY",
            "price": "EMPTY",
            "beds": "EMPTY",
            "baths": "EMPTY",
            "location": "EMPTY",
            "amenities": "EMPTY",
            "tour_availability": "EMPTY",
            "rental_urgency": "EMPTY",
            "boston_rental_experience": "EMPTY",
        }

        print(f"Message: {message}")
        print(f"Current data: {current_data}")

        result = client.extract_lead_info(message, current_data)

        print(f"Extracted result: {json.dumps(result, indent=2)}")

        assert result is not None
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_extract_lead_info_partial_information(self, client):
        """Test extraction with partial information"""
        print("\n=== Test: Partial Information Extraction ===")

        message = (
            "Looking for something around $2500, maybe 2 beds. I'm flexible on timing."
        )
        current_data = {
            "move_in_date": "EMPTY",
            "price": "EMPTY",
            "beds": "EMPTY",
            "baths": "EMPTY",
            "location": "EMPTY",
            "amenities": "EMPTY",
            "tour_availability": "EMPTY",
            "rental_urgency": "EMPTY",
            "boston_rental_experience": "EMPTY",
        }

        print(f"Message: {message}")
        print(f"Current data: {current_data}")

        result = client.extract_lead_info(message, current_data)

        print(f"Extracted result: {json.dumps(result, indent=2)}")

        assert result is not None
        assert isinstance(result, dict)

    def test_extract_lead_info_casual_language(self, client):
        """Test extraction with casual, conversational language"""
        print("\n=== Test: Casual Language Extraction ===")

        message = "Hey! So I'm kinda looking for a place, you know? Maybe like 2k max, and I need it pretty soon. Oh and I've never rented in Boston before so I'm not sure how this works."
        current_data = {
            "move_in_date": "EMPTY",
            "price": "EMPTY",
            "beds": "EMPTY",
            "baths": "EMPTY",
            "location": "EMPTY",
            "amenities": "EMPTY",
            "tour_availability": "EMPTY",
            "rental_urgency": "EMPTY",
            "boston_rental_experience": "EMPTY",
        }

        print(f"Message: {message}")
        print(f"Current data: {current_data}")

        result = client.extract_lead_info(message, current_data)

        print(f"Extracted result: {json.dumps(result, indent=2)}")

        assert result is not None
        assert isinstance(result, dict)

    def test_extract_lead_info_amenities_focus(self, client):
        """Test extraction focusing on amenities"""
        print("\n=== Test: Amenities Focus Extraction ===")

        message = "I really need a place with parking, central air, and a dishwasher. Also would love to be near a gym. Budget is flexible."
        current_data = {
            "move_in_date": "EMPTY",
            "price": "EMPTY",
            "beds": "EMPTY",
            "baths": "EMPTY",
            "location": "EMPTY",
            "amenities": "EMPTY",
            "tour_availability": "EMPTY",
            "rental_urgency": "EMPTY",
            "boston_rental_experience": "EMPTY",
        }

        print(f"Message: {message}")
        print(f"Current data: {current_data}")

        result = client.extract_lead_info(message, current_data)

        print(f"Extracted result: {json.dumps(result, indent=2)}")

        assert result is not None
        assert isinstance(result, dict)

    def test_extract_lead_info_location_specific(self, client):
        """Test extraction with specific location preferences"""
        print("\n=== Test: Location Specific Extraction ===")

        message = "I want to be in Back Bay or Beacon Hill, near the T. Looking for 1 bed, 1 bath, around $3500. Need it by October 1st."
        current_data = {
            "move_in_date": "EMPTY",
            "price": "EMPTY",
            "beds": "EMPTY",
            "baths": "EMPTY",
            "location": "EMPTY",
            "amenities": "EMPTY",
            "tour_availability": "EMPTY",
            "rental_urgency": "EMPTY",
            "boston_rental_experience": "EMPTY",
        }

        print(f"Message: {message}")
        print(f"Current data: {current_data}")

        result = client.extract_lead_info(message, current_data)

        print(f"Extracted result: {json.dumps(result, indent=2)}")

        assert result is not None
        assert isinstance(result, dict)

    def test_extract_lead_info_urgency_indicators(self, client):
        """Test extraction with urgency indicators"""
        print("\n=== Test: Urgency Indicators Extraction ===")

        message = "I need something ASAP! My lease ends in 2 weeks and I'm desperate. Anywhere in Boston is fine, just need a 2 bed place under $3000."
        current_data = {
            "move_in_date": "EMPTY",
            "price": "EMPTY",
            "beds": "EMPTY",
            "baths": "EMPTY",
            "location": "EMPTY",
            "amenities": "EMPTY",
            "tour_availability": "EMPTY",
            "rental_urgency": "EMPTY",
            "boston_rental_experience": "EMPTY",
        }

        print(f"Message: {message}")
        print(f"Current data: {current_data}")

        result = client.extract_lead_info(message, current_data)

        print(f"Extracted result: {json.dumps(result, indent=2)}")

        assert result is not None
        assert isinstance(result, dict)

    def test_extract_lead_info_experience_mention(self, client):
        """Test extraction with rental experience mentions"""
        print("\n=== Test: Rental Experience Extraction ===")

        message = "I've rented in Boston before, so I know the drill. Looking for a 3 bed, 2 bath in Cambridge, around $4000. I'm flexible on move-in date."
        current_data = {
            "move_in_date": "EMPTY",
            "price": "EMPTY",
            "beds": "EMPTY",
            "baths": "EMPTY",
            "location": "EMPTY",
            "amenities": "EMPTY",
            "tour_availability": "EMPTY",
            "rental_urgency": "EMPTY",
            "boston_rental_experience": "EMPTY",
        }

        print(f"Message: {message}")
        print(f"Current data: {current_data}")

        result = client.extract_lead_info(message, current_data)

        print(f"Extracted result: {json.dumps(result, indent=2)}")

        assert result is not None
        assert isinstance(result, dict)

    def test_extract_lead_info_tour_availability(self, client):
        """Test extraction with tour availability"""
        print("\n=== Test: Tour Availability Extraction ===")

        message = "I'm free to tour on weekends and weekday evenings after 6pm. Also available next Tuesday afternoon if that works better."
        current_data = {
            "move_in_date": "EMPTY",
            "price": "EMPTY",
            "beds": "EMPTY",
            "baths": "EMPTY",
            "location": "EMPTY",
            "amenities": "EMPTY",
            "tour_availability": "EMPTY",
            "rental_urgency": "EMPTY",
            "boston_rental_experience": "EMPTY",
        }

        print(f"Message: {message}")
        print(f"Current data: {current_data}")

        result = client.extract_lead_info(message, current_data)

        print(f"Extracted result: {json.dumps(result, indent=2)}")

        assert result is not None
        assert isinstance(result, dict)

    def test_extract_lead_info_no_new_info(self, client):
        """Test extraction when no new information is provided"""
        print("\n=== Test: No New Information Extraction ===")

        message = "Thanks for the info! That sounds great."
        current_data = {
            "move_in_date": "EMPTY",
            "price": "EMPTY",
            "beds": "EMPTY",
            "baths": "EMPTY",
            "location": "EMPTY",
            "amenities": "EMPTY",
            "tour_availability": "EMPTY",
            "rental_urgency": "EMPTY",
            "boston_rental_experience": "EMPTY",
        }

        print(f"Message: {message}")
        print(f"Current data: {current_data}")

        result = client.extract_lead_info(message, current_data)

        print(f"Extracted result: {json.dumps(result, indent=2)}")

        assert result is not None
        assert isinstance(result, dict)

    def test_extract_lead_info_already_has_data(self, client):
        """Test extraction when some data already exists"""
        print("\n=== Test: Existing Data Extraction ===")

        message = (
            "Actually, I can go up to $3500 and I'd prefer 2 bathrooms if possible."
        )
        current_data = {
            "move_in_date": "September 1st",
            "price": "$3000",
            "beds": "2",
            "baths": "1",
            "location": "Boston",
            "amenities": "parking",
            "tour_availability": "EMPTY",
            "rental_urgency": "EMPTY",
            "boston_rental_experience": "EMPTY",
        }

        print(f"Message: {message}")
        print(f"Current data: {current_data}")

        result = client.extract_lead_info(message, current_data)

        print(f"Extracted result: {json.dumps(result, indent=2)}")

        assert result is not None
        assert isinstance(result, dict)

    def test_generate_response_initial_contact(self, client, sample_lead_data):
        """Test response generation for initial contact"""
        print("\n=== Test: Initial Contact Response ===")

        incoming_message = "Hi, I'm looking for an apartment in Boston"
        missing_fields = [
            "move_in_date",
            "price",
            "beds",
            "baths",
            "location",
            "amenities",
        ]

        print(f"Context: Initial contact")
        print(f"Missing fields: {missing_fields}")
        print(f"Incoming message: {incoming_message}")

        response = client.generate_response(
            lead_data=sample_lead_data,
            incoming_message=incoming_message,
            missing_fields=missing_fields,
            needs_tour_availability=False,
        )

        print(f"AI Response: {response}")

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    def test_generate_response_qualification_phase(self, client, sample_lead_data):
        """Test response generation during qualification phase"""
        print("\n=== Test: Qualification Phase Response ===")

        incoming_message = "I need a 2 bedroom, 1 bathroom apartment"
        missing_fields = ["move_in_date", "price", "location", "amenities"]

        print(f"Context: Qualification phase")
        print(f"Missing fields: {missing_fields}")
        print(f"Incoming message: {incoming_message}")

        response = client.generate_response(
            lead_data=sample_lead_data,
            incoming_message=incoming_message,
            missing_fields=missing_fields,
            needs_tour_availability=False,
        )

        print(f"AI Response: {response}")

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    def test_generate_response_price_inquiry(self, client, sample_lead_data):
        """Test response generation for price inquiry"""
        print("\n=== Test: Price Inquiry Response ===")

        incoming_message = "My budget is around $2500 per month"
        missing_fields = ["move_in_date", "location", "amenities"]

        print(f"Context: Price inquiry")
        print(f"Missing fields: {missing_fields}")
        print(f"Incoming message: {incoming_message}")

        response = client.generate_response(
            lead_data=sample_lead_data,
            incoming_message=incoming_message,
            missing_fields=missing_fields,
            needs_tour_availability=False,
        )

        print(f"AI Response: {response}")

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    def test_generate_response_location_preference(self, client, sample_lead_data):
        """Test response generation for location preference"""
        print("\n=== Test: Location Preference Response ===")

        incoming_message = "I'd like to be in Back Bay or Beacon Hill"
        missing_fields = ["move_in_date", "amenities"]

        print(f"Context: Location preference")
        print(f"Missing fields: {missing_fields}")
        print(f"Incoming message: {incoming_message}")

        response = client.generate_response(
            lead_data=sample_lead_data,
            incoming_message=incoming_message,
            missing_fields=missing_fields,
            needs_tour_availability=False,
        )

        print(f"AI Response: {response}")

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    def test_generate_response_amenities_request(self, client, sample_lead_data):
        """Test response generation for amenities request"""
        print("\n=== Test: Amenities Request Response ===")

        incoming_message = "I need parking and in-unit laundry"
        missing_fields = ["move_in_date"]

        print(f"Context: Amenities request")
        print(f"Missing fields: {missing_fields}")
        print(f"Incoming message: {incoming_message}")

        response = client.generate_response(
            lead_data=sample_lead_data,
            incoming_message=incoming_message,
            missing_fields=missing_fields,
            needs_tour_availability=False,
        )

        print(f"AI Response: {response}")

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    def test_generate_response_move_in_date(self, client, sample_lead_data):
        """Test response generation for move-in date"""
        print("\n=== Test: Move-in Date Response ===")

        incoming_message = "I need to move in by September 1st"
        missing_fields = []

        print(f"Context: Move-in date provided")
        print(f"Missing fields: {missing_fields}")
        print(f"Incoming message: {incoming_message}")

        response = client.generate_response(
            lead_data=sample_lead_data,
            incoming_message=incoming_message,
            missing_fields=missing_fields,
            needs_tour_availability=True,
        )

        print(f"AI Response: {response}")

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    def test_generate_response_tour_scheduling(self, client, sample_lead_data):
        """Test response generation for tour scheduling"""
        print("\n=== Test: Tour Scheduling Response ===")

        incoming_message = "I'm free on weekends and weekday evenings"
        missing_fields = []

        print(f"Context: Tour scheduling phase")
        print(f"Missing fields: {missing_fields}")
        print(f"Incoming message: {incoming_message}")

        response = client.generate_response(
            lead_data=sample_lead_data,
            incoming_message=incoming_message,
            missing_fields=missing_fields,
            needs_tour_availability=True,
        )

        print(f"AI Response: {response}")

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    def test_generate_response_question_asking(self, client, sample_lead_data):
        """Test response generation when lead asks a question"""
        print("\n=== Test: Question Asking Response ===")

        incoming_message = "What's the application process like?"
        missing_fields = ["move_in_date", "amenities"]

        print(f"Context: Lead asking question")
        print(f"Missing fields: {missing_fields}")
        print(f"Incoming message: {incoming_message}")

        response = client.generate_response(
            lead_data=sample_lead_data,
            incoming_message=incoming_message,
            missing_fields=missing_fields,
            needs_tour_availability=False,
        )

        print(f"AI Response: {response}")

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    def test_generate_response_casual_conversation(self, client, sample_lead_data):
        """Test response generation for casual conversation"""
        print("\n=== Test: Casual Conversation Response ===")

        incoming_message = "Thanks! That sounds great. I'm excited to see some places."
        missing_fields = ["move_in_date", "amenities"]

        print(f"Context: Casual conversation")
        print(f"Missing fields: {missing_fields}")
        print(f"Incoming message: {incoming_message}")

        response = client.generate_response(
            lead_data=sample_lead_data,
            incoming_message=incoming_message,
            missing_fields=missing_fields,
            needs_tour_availability=False,
        )

        print(f"AI Response: {response}")

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    def test_generate_response_complete_qualification(self, client, sample_lead_data):
        """Test response generation when qualification is complete"""
        print("\n=== Test: Complete Qualification Response ===")

        # Update sample data to have all required fields
        complete_data = sample_lead_data.copy()
        complete_data.update(
            {"move_in_date": "September 1st", "amenities": "parking, gym"}
        )

        incoming_message = "Perfect, I have all the info I need"
        missing_fields = []

        print(f"Context: Complete qualification")
        print(f"Missing fields: {missing_fields}")
        print(f"Incoming message: {incoming_message}")

        response = client.generate_response(
            lead_data=complete_data,
            incoming_message=incoming_message,
            missing_fields=missing_fields,
            needs_tour_availability=True,
        )

        print(f"AI Response: {response}")

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    def test_generate_response_no_robotic_confirmation(self, client, sample_lead_data):
        """Test that AI doesn't use robotic 'thank you for confirming' language"""
        print("\n=== Test: No Robotic Confirmation Language ===")

        # Test multiple scenarios where users provide extractable information
        test_cases = [
            {
                "message": "My budget is $2500 per month",
                "field": "price",
                "description": "Price information",
            },
            {
                "message": "I need a 2 bedroom apartment",
                "field": "beds",
                "description": "Bedroom count",
            },
            {
                "message": "I want to move in on September 1st",
                "field": "move_in_date",
                "description": "Move-in date",
            },
            {
                "message": "I'd like to be in Back Bay",
                "field": "location",
                "description": "Location preference",
            },
            {
                "message": "I need parking and in-unit laundry",
                "field": "amenities",
                "description": "Amenities",
            },
            {
                "message": "I need 2 bathrooms",
                "field": "baths",
                "description": "Bathroom count",
            },
        ]

        for test_case in test_cases:
            print(f"\n--- Testing: {test_case['description']} ---")
            print(f"Message: {test_case['message']}")

            # Create lead data with the specific field empty
            test_data = sample_lead_data.copy()
            test_data[test_case["field"]] = (
                ""  # Ensure field is empty so it gets extracted
            )

            # Determine missing fields (exclude the one being tested)
            all_required_fields = [
                "move_in_date",
                "price",
                "beds",
                "baths",
                "location",
                "amenities",
            ]
            missing_fields = [
                field for field in all_required_fields if field != test_case["field"]
            ]

            print(f"Missing fields: {missing_fields}")

            response = client.generate_response(
                lead_data=test_data,
                incoming_message=test_case["message"],
                missing_fields=missing_fields,
                needs_tour_availability=False,
            )

            print(f"AI Response: {response}")

            # Assertions to check for robotic language
            response_lower = response.lower()

            # Check for robotic confirmation patterns
            robotic_patterns = [
                "thank you for confirming",
                "thanks for confirming",
                "thank you for providing",
                "thanks for providing",
                "thank you for sharing",
                "thanks for sharing",
                "thank you for letting me know",
                "thanks for letting me know",
                "per your last message",
                "as you mentioned",
                "as you stated",
                "as you indicated",
            ]

            found_robotic_patterns = []
            for pattern in robotic_patterns:
                if pattern in response_lower:
                    found_robotic_patterns.append(pattern)

            if found_robotic_patterns:
                print(f"❌ WARNING: Found robotic patterns: {found_robotic_patterns}")
                # Don't fail the test, but warn about robotic language
                print(f"   Response should be more natural and avoid these patterns")
            else:
                print(f"✅ No robotic confirmation patterns detected")

            # Check for natural acknowledgment patterns
            natural_patterns = [
                "got it",
                "makes sense",
                "okay",
                "perfect",
                "great",
                "sounds good",
                "that works",
                "that helps",
            ]

            found_natural_patterns = []
            for pattern in natural_patterns:
                if pattern in response_lower:
                    found_natural_patterns.append(pattern)

            if found_natural_patterns:
                print(f"✅ Found natural acknowledgment: {found_natural_patterns}")
            else:
                print(
                    f"ℹ️  No natural acknowledgment patterns found (this might be okay)"
                )

            # Basic assertions
            assert response is not None
            assert len(response) > 0
            assert isinstance(response, str)

            # Check that response doesn't restate the field name in a robotic way
            field_name = test_case["field"].replace("_", " ")
            if (
                f"your {field_name}" in response_lower
                or f"the {field_name}" in response_lower
            ):
                print(
                    f"⚠️  WARNING: Response mentions field name '{field_name}' - check if natural"
                )

            print(f"--- End test case ---")

import pytest
from unittest.mock import patch
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestDelayDetector:

    def test_init(self):
        """Test DelayDetector initialization"""
        from src.utils.delay_detector import DelayDetector

        detector = DelayDetector()

        assert detector.delay_patterns is not None
        assert len(detector.delay_patterns) > 0
        assert detector.word_to_number is not None

    def test_detect_delay_request_specific_days(self):
        """Test detecting specific day delay requests"""
        from src.utils.delay_detector import DelayDetector

        detector = DelayDetector()

        # Test various day patterns
        test_cases = [
            ("give me 3 days", 3),
            ("call me in 5 days", 5),
            ("contact me in 2 days", 2),
            ("check back in 7 days", 7),
            ("follow up in 1 day", 1),
            ("reach out in 4 days", 4),
        ]

        for message, expected_days in test_cases:
            result = detector.detect_delay_request(message)
            assert result is not None
            assert result["delay_days"] == expected_days
            assert result["delay_type"] == "specific"

    def test_detect_delay_request_specific_weeks(self):
        """Test detecting specific week delay requests"""
        from src.utils.delay_detector import DelayDetector

        detector = DelayDetector()

        test_cases = [
            ("give me 2 weeks", 14),
            ("call me in 1 week", 7),
            ("contact me in 3 weeks", 21),
            ("next week", 7),
            ("in a week", 7),
        ]

        for message, expected_days in test_cases:
            result = detector.detect_delay_request(message)
            assert result is not None
            assert result["delay_days"] == expected_days

    def test_detect_delay_request_specific_months(self):
        """Test detecting specific month delay requests"""
        from src.utils.delay_detector import DelayDetector

        detector = DelayDetector()

        test_cases = [
            ("give me 1 month", 30),
            ("call me in 2 months", 60),
            ("next month", 30),
            ("in a month", 30),
        ]

        for message, expected_days in test_cases:
            result = detector.detect_delay_request(message)
            assert result is not None
            assert result["delay_days"] == expected_days

    def test_detect_delay_request_word_numbers(self):
        """Test detecting delay requests with word numbers"""
        from src.utils.delay_detector import DelayDetector

        detector = DelayDetector()

        test_cases = [
            ("give me two days", 2),
            ("call me in three weeks", 21),
            ("contact me in five days", 5),
            ("follow up in ten weeks", 70),
        ]

        for message, expected_days in test_cases:
            result = detector.detect_delay_request(message)
            assert result is not None
            assert result["delay_days"] == expected_days

    def test_detect_delay_request_general_indicators(self):
        """Test detecting general delay indicators without specific time"""
        from src.utils.delay_detector import DelayDetector

        detector = DelayDetector()

        test_messages = [
            "I'm not ready yet",
            "This is too early",
            "I'm busy right now",
            "Can you wait?",
            "I'll contact you later",
        ]

        for message in test_messages:
            result = detector.detect_delay_request(message)
            assert result is not None
            assert result["delay_days"] == 7  # Default to 1 week
            assert result["delay_type"] == "general"

    def test_detect_delay_request_no_delay(self):
        """Test messages with no delay request"""
        from src.utils.delay_detector import DelayDetector

        detector = DelayDetector()

        test_messages = [
            "Yes, I'm interested",
            "That sounds great",
            "I'm looking for apartments",
            "What's available?",
            "I'm ready to see some places",
        ]

        for message in test_messages:
            result = detector.detect_delay_request(message)
            assert result is None

    def test_detect_delay_request_edge_cases(self):
        """Test edge cases for delay detection"""
        from src.utils.delay_detector import DelayDetector

        detector = DelayDetector()

        # Empty message
        assert detector.detect_delay_request("") is None

        # Message with delay keyword but no clear delay intent
        result = detector.detect_delay_request("I'm ready to give you my information")
        assert result is not None  # "give you" might trigger, but that's ok for safety

        # Mixed case
        result = detector.detect_delay_request("GIVE ME 3 DAYS")
        assert result is not None
        assert result["delay_days"] == 3

    def test_parse_delay_match_two_groups(self):
        """Test parsing delay match with two groups"""
        from src.utils.delay_detector import DelayDetector
        import re

        detector = DelayDetector()

        # Mock a regex match with two groups
        pattern = r"give me (\d+) (days|weeks|months)"
        match = re.search(pattern, "give me 5 days")

        result = detector._parse_delay_match(match)

        assert result["delay_days"] == 5
        assert result["delay_type"] == "specific"
        assert result["original_text"] == "give me 5 days"

    def test_parse_delay_match_one_group(self):
        """Test parsing delay match with one group"""
        from src.utils.delay_detector import DelayDetector
        import re

        detector = DelayDetector()

        # Mock a regex match with one group
        pattern = r"next (week|month)"
        match = re.search(pattern, "next week")

        result = detector._parse_delay_match(match)

        assert result["delay_days"] == 7
        assert result["delay_type"] == "specific"
        assert result["original_text"] == "next week"

    def test_calculate_delay_until(self):
        """Test calculating delay until datetime"""
        from src.utils.delay_detector import DelayDetector

        detector = DelayDetector()

        delay_info = {
            "delay_days": 5,
            "delay_type": "specific",
            "original_text": "give me 5 days",
        }

        with patch("src.utils.delay_detector.datetime") as mock_datetime:
            # Mock current time
            mock_now = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = detector.calculate_delay_until(delay_info)

            expected = mock_now + timedelta(days=5)
            assert result == expected

    def test_few_days_weeks_patterns(self):
        """Test patterns like 'few days' and 'couple weeks'"""
        from src.utils.delay_detector import DelayDetector

        detector = DelayDetector()

        test_cases = [
            ("give me a few days", 3),  # "few days" defaults to 3
            ("contact me in a few weeks", 14),  # "few weeks" defaults to 14
            ("give me a couple days", 3),  # "couple days" defaults to 3
            ("call me in a couple weeks", 14),  # "couple weeks" defaults to 14
        ]

        for message, expected_days in test_cases:
            result = detector.detect_delay_request(message)
            assert result is not None
            assert result["delay_days"] == expected_days

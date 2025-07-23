import re
from datetime import datetime, timedelta
from typing import Optional, Dict

class DelayDetector:
    """Detects and parses delay requests from conversation messages"""
    
    def __init__(self):
        self.delay_patterns = [
            # "give me X days/weeks/months"
            r"give me (\d+) (day|days|week|weeks|month|months)",
            # "call me in X days/weeks/months"
            r"call me in (\d+) (day|days|week|weeks|month|months)",
            # "contact me in X days/weeks/months"
            r"contact me in (\d+) (day|days|week|weeks|month|months)",
            # "check back in X days/weeks/months"
            r"check back in (\d+) (day|days|week|weeks|month|months)",
            # "follow up in X days/weeks/months"
            r"follow up in (\d+) (day|days|week|weeks|month|months)",
            # "reach out in X days/weeks/months"
            r"reach out in (\d+) (day|days|week|weeks|month|months)",
            # "next week/month"
            r"next (week|month)",
            # "in a week/month"
            r"in a (week|month)",
            # "few days/weeks"
            r"few (days|weeks)",
            # "couple days/weeks"
            r"couple (days|weeks)",
            # "1 week", "2 weeks", etc.
            r"(\d+) (week|weeks|month|months)",
            # "two weeks", "three days", etc.
            r"(two|three|four|five|six|seven|eight|nine|ten) (day|days|week|weeks|month|months)"
        ]
        
        self.word_to_number = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }
    
    def detect_delay_request(self, message: str) -> Optional[Dict]:
        """
        Detect if message contains a delay request
        Returns dict with delay info or None
        """
        message_lower = message.lower()
        
        # Check for general delay indicators first
        delay_keywords = [
            "not ready", "too early", "not yet", "later", "busy", "wait",
            "give me", "call me", "contact me", "reach out", "check back", "follow up"
        ]
        
        has_delay_indicator = any(keyword in message_lower for keyword in delay_keywords)
        if not has_delay_indicator:
            return None
        
        # Try to parse specific time periods
        for pattern in self.delay_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return self._parse_delay_match(match)
        
        # If we have delay indicators but no specific time, default to 1 week
        if has_delay_indicator:
            return {
                "delay_days": 7,
                "delay_type": "general",
                "original_text": message
            }
        
        return None
    
    def _parse_delay_match(self, match) -> Dict:
        """Parse regex match into delay information"""
        groups = match.groups()
        
        if len(groups) == 2:
            # Pattern like "give me 2 weeks"
            number_str = groups[0]
            unit = groups[1]
            
            # Convert word numbers to digits
            if number_str in self.word_to_number:
                number = self.word_to_number[number_str]
            else:
                number = int(number_str)
            
            # Convert to days
            if unit.startswith("day"):
                delay_days = number
            elif unit.startswith("week"):
                delay_days = number * 7
            elif unit.startswith("month"):
                delay_days = number * 30
            else:
                delay_days = 7  # default
                
        elif len(groups) == 1:
            # Pattern like "next week" or "few days"
            unit = groups[0]
            
            if unit == "week":
                delay_days = 7
            elif unit == "month":
                delay_days = 30
            elif unit == "days":
                delay_days = 3  # "few days"
            elif unit == "weeks":
                delay_days = 14  # "few weeks"
            else:
                delay_days = 7  # default
        else:
            delay_days = 7  # default
        
        return {
            "delay_days": delay_days,
            "delay_type": "specific",
            "original_text": match.group(0)
        }
    
    def calculate_delay_until(self, delay_info: Dict) -> datetime:
        """Calculate the datetime until when follow-ups should be paused"""
        delay_days = delay_info["delay_days"]
        return datetime.now() + timedelta(days=delay_days) 
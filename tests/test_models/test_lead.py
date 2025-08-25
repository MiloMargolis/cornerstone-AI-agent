import pytest
from datetime import datetime
from src.models.lead import Lead, LeadStatus


class TestLead:
    """Test cases for Lead data model"""
    
    def test_lead_creation_with_required_fields(self):
        """Test creating a lead with only required fields"""
        lead = Lead(phone="+1234567890")
        
        assert lead.phone == "+1234567890"
        assert lead.name is None
        assert lead.email is None
        assert lead.tour_ready is False
        assert lead.status == LeadStatus.NEW
        assert lead.follow_up_count == 0
        assert lead.follow_up_stage == "scheduled"
        assert lead.created_at is not None
        assert lead.updated_at is not None
    
    def test_lead_creation_with_all_fields(self):
        """Test creating a lead with all fields"""
        lead = Lead(
            phone="+1234567890",
            name="John Doe",
            email="john@example.com",
            beds="2",
            baths="1",
            move_in_date="2024-02-01",
            price="2000",
            location="Boston",
            amenities="Parking, Gym",
            tour_availability="Tuesday 2pm",
            tour_ready=True,
            status=LeadStatus.TOUR_READY,
            follow_up_count=3,
            follow_up_stage="final",
            rental_urgency="High",
            boston_rental_experience="First time"
        )
        
        assert lead.phone == "+1234567890"
        assert lead.name == "John Doe"
        assert lead.email == "john@example.com"
        assert lead.beds == "2"
        assert lead.baths == "1"
        assert lead.move_in_date == "2024-02-01"
        assert lead.price == "2000"
        assert lead.location == "Boston"
        assert lead.amenities == "Parking, Gym"
        assert lead.tour_availability == "Tuesday 2pm"
        assert lead.tour_ready is True
        assert lead.status == LeadStatus.TOUR_READY
        assert lead.follow_up_count == 3
        assert lead.follow_up_stage == "final"
        assert lead.rental_urgency == "High"
        assert lead.boston_rental_experience == "First time"
    
    def test_lead_creation_missing_phone(self):
        """Test creating a lead without phone number raises error"""
        with pytest.raises(ValueError, match="Phone number is required"):
            Lead(phone="")
    
    def test_lead_creation_with_none_phone(self):
        """Test creating a lead with None phone number raises error"""
        with pytest.raises(ValueError, match="Phone number is required"):
            Lead(phone=None)
    
    def test_lead_is_qualified_all_fields_present(self):
        """Test lead qualification when all required fields are present"""
        lead = Lead(
            phone="+1234567890",
            move_in_date="2024-02-01",
            price="2000",
            beds="2",
            baths="1",
            location="Boston",
            amenities="Parking"
        )
        
        assert lead.is_qualified is True
    
    def test_lead_is_qualified_missing_fields(self):
        """Test lead qualification when required fields are missing"""
        lead = Lead(
            phone="+1234567890",
            move_in_date="2024-02-01",
            price="2000",
            # Missing beds, baths, location, amenities
        )
        
        assert lead.is_qualified is False
    
    def test_lead_is_qualified_empty_fields(self):
        """Test lead qualification when required fields are empty"""
        lead = Lead(
            phone="+1234567890",
            move_in_date="",
            price="",
            beds="",
            baths="",
            location="",
            amenities=""
        )
        
        assert lead.is_qualified is False
    
    def test_lead_is_qualified_whitespace_fields(self):
        """Test lead qualification when required fields are whitespace"""
        lead = Lead(
            phone="+1234567890",
            move_in_date="   ",
            price="   ",
            beds="   ",
            baths="   ",
            location="   ",
            amenities="   "
        )
        
        assert lead.is_qualified is False
    
    def test_missing_required_fields(self):
        """Test getting list of missing required fields"""
        lead = Lead(
            phone="+1234567890",
            move_in_date="2024-02-01",
            price="2000",
            # Missing beds, baths, location, amenities
        )
        
        missing_fields = lead.missing_required_fields
        assert "beds" in missing_fields
        assert "baths" in missing_fields
        assert "location" in missing_fields
        assert "amenities" in missing_fields
        assert "move_in_date" not in missing_fields
        assert "price" not in missing_fields
    
    def test_missing_optional_fields(self):
        """Test getting list of missing optional fields"""
        lead = Lead(
            phone="+1234567890",
            # Missing rental_urgency, boston_rental_experience
        )
        
        missing_fields = lead.missing_optional_fields
        assert "rental_urgency" in missing_fields
        assert "boston_rental_experience" in missing_fields
    
    def test_missing_optional_fields_some_present(self):
        """Test getting list of missing optional fields when some are present"""
        lead = Lead(
            phone="+1234567890",
            rental_urgency="High"
            # Missing boston_rental_experience
        )
        
        missing_fields = lead.missing_optional_fields
        assert "rental_urgency" not in missing_fields
        assert "boston_rental_experience" in missing_fields
    
    def test_needs_tour_availability_qualified_no_tour_ready(self):
        """Test needs_tour_availability when qualified but not tour ready"""
        lead = Lead(
            phone="+1234567890",
            move_in_date="2024-02-01",
            price="2000",
            beds="2",
            baths="1",
            location="Boston",
            amenities="Parking",
            tour_ready=False,
            tour_availability=""  # Empty
        )
        
        assert lead.needs_tour_availability is True
    
    def test_needs_tour_availability_qualified_tour_ready(self):
        """Test needs_tour_availability when qualified and tour ready"""
        lead = Lead(
            phone="+1234567890",
            move_in_date="2024-02-01",
            price="2000",
            beds="2",
            baths="1",
            location="Boston",
            amenities="Parking",
            tour_ready=True
        )
        
        assert lead.needs_tour_availability is False
    
    def test_needs_tour_availability_not_qualified(self):
        """Test needs_tour_availability when not qualified"""
        lead = Lead(
            phone="+1234567890",
            # Missing required fields
            tour_ready=False
        )
        
        assert lead.needs_tour_availability is False
    
    def test_needs_tour_availability_has_tour_availability(self):
        """Test needs_tour_availability when tour availability is provided"""
        lead = Lead(
            phone="+1234567890",
            move_in_date="2024-02-01",
            price="2000",
            beds="2",
            baths="1",
            location="Boston",
            amenities="Parking",
            tour_ready=False,
            tour_availability="Tuesday 2pm"  # Has value
        )
        
        assert lead.needs_tour_availability is False
    
    def test_to_dict(self):
        """Test converting lead to dictionary"""
        lead = Lead(
            phone="+1234567890",
            name="John Doe",
            email="john@example.com",
            beds="2",
            baths="1",
            move_in_date="2024-02-01",
            price="2000",
            location="Boston",
            amenities="Parking",
            tour_availability="Tuesday 2pm",
            tour_ready=True,
            follow_up_count=3,
            follow_up_stage="final",
            rental_urgency="High",
            boston_rental_experience="First time",
            chat_history="Test conversation"
        )
        
        lead_dict = lead.to_dict()
        
        assert lead_dict["phone"] == "+1234567890"
        assert lead_dict["name"] == "John Doe"
        assert lead_dict["email"] == "john@example.com"
        assert lead_dict["beds"] == "2"
        assert lead_dict["baths"] == "1"
        assert lead_dict["move_in_date"] == "2024-02-01"
        assert lead_dict["price"] == "2000"
        assert lead_dict["location"] == "Boston"
        assert lead_dict["amenities"] == "Parking"
        assert lead_dict["tour_availability"] == "Tuesday 2pm"
        assert lead_dict["tour_ready"] is True
        assert lead_dict["follow_up_count"] == 3
        assert lead_dict["follow_up_stage"] == "final"
        assert lead_dict["rental_urgency"] == "High"
        assert lead_dict["boston_rental_experience"] == "First time"
        assert lead_dict["chat_history"] == "Test conversation"
        assert lead_dict["created_at"] is not None
        assert lead_dict["updated_at"] is not None
    
    def test_to_dict_with_none_values(self):
        """Test converting lead to dictionary with None values"""
        lead = Lead(phone="+1234567890")
        
        lead_dict = lead.to_dict()
        
        assert lead_dict["name"] == ""
        assert lead_dict["email"] == ""
        assert lead_dict["beds"] == ""
        assert lead_dict["baths"] == ""
        assert lead_dict["move_in_date"] == ""
        assert lead_dict["price"] == ""
        assert lead_dict["location"] == ""
        assert lead_dict["amenities"] == ""
        assert lead_dict["tour_availability"] == ""
        assert lead_dict["rental_urgency"] == ""
        assert lead_dict["boston_rental_experience"] == ""
        assert lead_dict["chat_history"] == ""
    
    def test_from_dict(self):
        """Test creating lead from dictionary"""
        lead_data = {
            "phone": "+1234567890",
            "name": "John Doe",
            "email": "john@example.com",
            "beds": "2",
            "baths": "1",
            "move_in_date": "2024-02-01",
            "price": "2000",
            "location": "Boston",
            "amenities": "Parking",
            "tour_availability": "Tuesday 2pm",
            "tour_ready": True,
            "follow_up_count": 3,
            "follow_up_stage": "final",
            "rental_urgency": "High",
            "boston_rental_experience": "First time",
            "chat_history": "Test conversation",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_contacted": datetime.now()
        }
        
        lead = Lead.from_dict(lead_data)
        
        assert lead.phone == "+1234567890"
        assert lead.name == "John Doe"
        assert lead.email == "john@example.com"
        assert lead.beds == "2"
        assert lead.baths == "1"
        assert lead.move_in_date == "2024-02-01"
        assert lead.price == "2000"
        assert lead.location == "Boston"
        assert lead.amenities == "Parking"
        assert lead.tour_availability == "Tuesday 2pm"
        assert lead.tour_ready is True
        assert lead.follow_up_count == 3
        assert lead.follow_up_stage == "final"
        assert lead.rental_urgency == "High"
        assert lead.boston_rental_experience == "First time"
        assert lead.chat_history == "Test conversation"
        assert lead.created_at is not None
        assert lead.updated_at is not None
        assert lead.last_contacted is not None
    
    def test_from_dict_with_missing_fields(self):
        """Test creating lead from dictionary with missing fields"""
        lead_data = {
            "phone": "+1234567890"
            # Missing other fields
        }
        
        lead = Lead.from_dict(lead_data)
        
        assert lead.phone == "+1234567890"
        assert lead.name is None
        assert lead.email is None
        assert lead.tour_ready is False
        assert lead.follow_up_count == 0
        assert lead.follow_up_stage == "scheduled"
        assert lead.chat_history == ""
    
    def test_lead_status_enum(self):
        """Test LeadStatus enum values"""
        assert LeadStatus.NEW.value == "new"
        assert LeadStatus.QUALIFYING.value == "qualifying"
        assert LeadStatus.TOUR_SCHEDULING.value == "tour_scheduling"
        assert LeadStatus.TOUR_READY.value == "tour_ready"
        assert LeadStatus.COMPLETE.value == "complete"

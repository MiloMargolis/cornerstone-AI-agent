from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LeadStatus(Enum):
    """Lead qualification status"""
    NEW = "new"
    QUALIFYING = "qualifying"
    TOUR_SCHEDULING = "tour_scheduling"
    TOUR_READY = "tour_ready"
    COMPLETE = "complete"


@dataclass
class Lead:
    """Lead data model with validation and business logic"""
    
    # Required fields
    phone: str
    
    # Optional fields
    name: Optional[str] = None
    email: Optional[str] = None
    beds: Optional[str] = None
    baths: Optional[str] = None
    move_in_date: Optional[str] = None
    price: Optional[str] = None
    location: Optional[str] = None
    amenities: Optional[str] = None
    tour_availability: Optional[str] = None
    
    # Status fields
    tour_ready: bool = False
    status: LeadStatus = LeadStatus.NEW
    
    # Follow-up fields
    follow_up_count: int = 0
    follow_up_stage: str = "scheduled"
    next_follow_up_time: Optional[datetime] = None
    follow_up_paused_until: Optional[datetime] = None
    
    # Optional qualification fields
    rental_urgency: Optional[str] = None
    boston_rental_experience: Optional[str] = None
    
    # Metadata
    chat_history: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_contacted: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate and set defaults after initialization"""
        if not self.phone:
            raise ValueError("Phone number is required")
        
        if not self.created_at:
            self.created_at = datetime.now()
        
        self.updated_at = datetime.now()
    
    @property
    def is_qualified(self) -> bool:
        """Check if lead has all required qualification fields"""
        required_fields = ["move_in_date", "price", "beds", "baths", "location", "amenities"]
        return all(getattr(self, field) and str(getattr(self, field)).strip() 
                  for field in required_fields)
    
    @property
    def missing_required_fields(self) -> list[str]:
        """Get list of missing required fields"""
        required_fields = ["move_in_date", "price", "beds", "baths", "location", "amenities"]
        return [field for field in required_fields 
                if not getattr(self, field) or not str(getattr(self, field)).strip()]
    
    @property
    def missing_optional_fields(self) -> list[str]:
        """Get list of missing optional fields"""
        optional_fields = ["rental_urgency", "boston_rental_experience"]
        return [field for field in optional_fields 
                if not getattr(self, field) or not str(getattr(self, field)).strip()]
    
    @property
    def needs_tour_availability(self) -> bool:
        """Check if lead needs tour availability information"""
        return (self.is_qualified and 
                not self.tour_ready and 
                (not self.tour_availability or not self.tour_availability.strip()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "phone": self.phone,
            "name": self.name or "",
            "email": self.email or "",
            "beds": self.beds or "",
            "baths": self.baths or "",
            "move_in_date": self.move_in_date or "",
            "price": self.price or "",
            "location": self.location or "",
            "amenities": self.amenities or "",
            "tour_availability": self.tour_availability or "",
            "tour_ready": self.tour_ready,
            "follow_up_count": self.follow_up_count,
            "follow_up_stage": self.follow_up_stage,
            "next_follow_up_time": self.next_follow_up_time,
            "follow_up_paused_until": self.follow_up_paused_until,
            "rental_urgency": self.rental_urgency or "",
            "boston_rental_experience": self.boston_rental_experience or "",
            "chat_history": self.chat_history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_contacted": self.last_contacted,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lead":
        """Create Lead instance from dictionary"""
        return cls(
            phone=data["phone"],
            name=data.get("name"),
            email=data.get("email"),
            beds=data.get("beds"),
            baths=data.get("baths"),
            move_in_date=data.get("move_in_date"),
            price=data.get("price"),
            location=data.get("location"),
            amenities=data.get("amenities"),
            tour_availability=data.get("tour_availability"),
            tour_ready=data.get("tour_ready", False),
            follow_up_count=data.get("follow_up_count", 0),
            follow_up_stage=data.get("follow_up_stage", "scheduled"),
            next_follow_up_time=data.get("next_follow_up_time"),
            follow_up_paused_until=data.get("follow_up_paused_until"),
            rental_urgency=data.get("rental_urgency"),
            boston_rental_experience=data.get("boston_rental_experience"),
            chat_history=data.get("chat_history", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            last_contacted=data.get("last_contacted"),
        )

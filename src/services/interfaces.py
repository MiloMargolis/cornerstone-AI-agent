from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Any
from models.lead import Lead
from models.webhook import WebhookEvent


class ILeadRepository(ABC):
    """Interface for lead data access"""

    @abstractmethod
    async def get_by_phone(self, phone: str) -> Optional[Lead]:
        """Get lead by phone number"""
        pass

    @abstractmethod
    async def create(self, lead: Lead) -> Optional[Lead]:
        """Create a new lead"""
        pass

    @abstractmethod
    async def update(self, phone: str, updates: Dict[str, Any]) -> Optional[Lead]:
        """Update lead with new information"""
        pass

    @abstractmethod
    async def add_message_to_history(
        self, phone: str, message: str, sender: str
    ) -> bool:
        """Add message to lead's chat history"""
        pass

    @abstractmethod
    async def schedule_follow_up(self, phone: str, days: int, stage: str) -> bool:
        """Schedule a follow-up for a lead"""
        pass

    @abstractmethod
    async def pause_follow_up_until(self, phone: str, pause_until: str) -> bool:
        """Pause follow-ups until specified time"""
        pass

    @abstractmethod
    async def set_tour_ready(self, phone: str) -> bool:
        """Mark lead as tour ready"""
        pass

    @abstractmethod
    async def get_leads_needing_follow_up(self) -> List[Lead]:
        """Get leads that need follow-up messages"""
        pass

    @abstractmethod
    async def get_missing_fields(self, lead: Lead) -> List[str]:
        """Get list of missing required fields for a lead"""
        pass

    @abstractmethod
    async def get_missing_optional_fields(self, lead: Lead) -> List[str]:
        """Get list of missing optional fields for a lead"""
        pass

    @abstractmethod
    async def needs_tour_availability(self, lead: Lead) -> bool:
        """Check if lead needs tour availability information"""
        pass


class IMessagingService(ABC):
    """Interface for messaging operations"""

    @abstractmethod
    async def send_sms(self, to: str, message: str) -> bool:
        """Send SMS message"""
        pass

    @abstractmethod
    async def send_agent_notification(self, agent_phone: str, message: str) -> bool:
        """Send notification to agent"""
        pass


class IAIService(ABC):
    """Interface for AI operations"""

    @abstractmethod
    async def extract_lead_info(self, message: str, lead: Lead) -> Dict[str, Any]:
        """Extract lead information from message"""
        pass

    @abstractmethod
    async def generate_response(
        self,
        lead: Lead,
        message: str,
        missing_fields: List[str],
        needs_tour_availability: bool = False,
        missing_optional: Optional[List[str]] = None,
        extracted_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate AI response based on lead state"""
        pass

    @abstractmethod
    async def generate_delay_response(self, delay_info: Dict[str, Any]) -> str:
        """Generate response for delay requests"""
        pass


class IDelayDetectionService(ABC):
    """Interface for delay detection"""

    @abstractmethod
    async def detect_delay_request(self, message: str) -> Optional[Dict[str, Any]]:
        """Detect if message contains delay request"""
        pass

    @abstractmethod
    async def calculate_delay_until(self, delay_info: Dict[str, Any]) -> str:
        """Calculate delay until time"""
        pass


class IEventProcessor(ABC):
    """Interface for event processing"""

    @abstractmethod
    async def process_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process webhook event"""
        pass

    @abstractmethod
    async def validate_event(self, event: WebhookEvent) -> bool:
        """Validate webhook event"""
        pass

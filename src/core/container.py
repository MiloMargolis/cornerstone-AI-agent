import os
from typing import Dict, Any, Type
from src.services.interfaces import (
    ILeadRepository, IMessagingService, IAIService, 
    IDelayDetectionService, IEventProcessor
)
from src.services.database.lead_repository import LeadRepository
from src.core.lead_processor import LeadProcessor
from src.core.event_processor import EventProcessor


class ServiceContainer:
    """Dependency injection container for managing service dependencies"""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
    
    def register(self, interface: Type, implementation: Any):
        """Register a service implementation"""
        self._services[interface] = implementation
    
    def register_singleton(self, interface: Type, implementation: Any):
        """Register a singleton service implementation"""
        self._singletons[interface] = implementation
    
    def resolve(self, interface: Type) -> Any:
        """Resolve a service implementation"""
        # Check if it's a singleton first
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Check if it's a regular service
        if interface in self._services:
            return self._services[interface]
        
        raise ValueError(f"No implementation registered for {interface}")
    
    def build_services(self):
        """Build and configure all services with their dependencies"""
        # Register core services
        self._register_core_services()
        
        # Register business logic services
        self._register_business_services()
        
        # Register event processing services
        self._register_event_services()
    
    def _register_core_services(self):
        """Register core infrastructure services"""
        # Database services
        lead_repository = LeadRepository()
        self.register_singleton(ILeadRepository, lead_repository)
        
        # Note: Other services (messaging, AI, delay detection) would be registered here
        # For now, we'll use the existing implementations
        # In a full implementation, you would create service implementations that implement the interfaces
    
    def _register_business_services(self):
        """Register business logic services"""
        # Lead processor depends on all other services
        lead_repository = self.resolve(ILeadRepository)
        
        # For now, we'll create placeholder services
        # In a real implementation, you would create proper implementations
        messaging_service = self._create_messaging_service()
        ai_service = self._create_ai_service()
        delay_detection_service = self._create_delay_detection_service()
        
        lead_processor = LeadProcessor(
            lead_repository=lead_repository,
            messaging_service=messaging_service,
            ai_service=ai_service,
            delay_detection_service=delay_detection_service
        )
        
        self.register_singleton(LeadProcessor, lead_processor)
    
    def _register_event_services(self):
        """Register event processing services"""
        lead_processor = self.resolve(LeadProcessor)
        
        event_processor = EventProcessor(lead_processor=lead_processor)
        self.register_singleton(IEventProcessor, event_processor)
    
    def _create_messaging_service(self) -> IMessagingService:
        """Create messaging service implementation"""
        # Check if we should use mock service
        if os.getenv("MOCK_TELNX", "0") == "1":
            from src.services.messaging.telnyx_service import MockTelnyxService
            return MockTelnyxService()
        else:
            from src.services.messaging.telnyx_service import TelnyxService
            return TelnyxService()
    
    def _create_ai_service(self) -> IAIService:
        """Create AI service implementation"""
        from src.services.ai.openai_service import OpenAIService
        return OpenAIService()
    
    def _create_delay_detection_service(self) -> IDelayDetectionService:
        """Create delay detection service implementation"""
        from src.services.delay_detection.delay_detection_service import DelayDetectionService
        return DelayDetectionService()


# Global service container instance
container = ServiceContainer()

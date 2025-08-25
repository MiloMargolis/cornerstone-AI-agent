import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from src.core.container import ServiceContainer
from src.services.interfaces import ILeadRepository, IMessagingService, IAIService, IDelayDetectionService


class TestServiceContainer:
    """Test cases for ServiceContainer dependency injection"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.container = ServiceContainer()
    
    def test_register_and_resolve_service(self):
        """Test registering and resolving a service"""
        mock_service = Mock()
        self.container.register(ILeadRepository, mock_service)
        
        resolved_service = self.container.resolve(ILeadRepository)
        assert resolved_service == mock_service
    
    def test_resolve_unregistered_service_raises_error(self):
        """Test resolving an unregistered service raises error"""
        with pytest.raises(ValueError, match="No implementation registered for"):
            self.container.resolve(ILeadRepository)
    
    @patch.dict(os.environ, {'MOCK_TELNX': '1'})
    @patch('src.core.container.LeadRepository')
    @patch('src.services.messaging.telnyx_service.MockTelnyxService')
    @patch('src.services.ai.openai_service.OpenAIService')
    @patch('src.services.delay_detection.delay_detection_service.DelayDetectionService')
    @patch('src.core.container.LeadProcessor')
    @patch('src.core.container.EventProcessor')
    def test_build_services_success(self, mock_event_processor, mock_lead_processor, 
                                   mock_delay_service, mock_ai_service, 
                                   mock_messaging_service, mock_lead_repo):
        """Test building all services successfully"""
        # Setup mocks
        mock_lead_repo_instance = Mock()
        mock_lead_repo.return_value = mock_lead_repo_instance
        
        mock_messaging_instance = Mock()
        mock_messaging_service.return_value = mock_messaging_instance
        
        mock_ai_instance = Mock()
        mock_ai_service.return_value = mock_ai_instance
        
        mock_delay_instance = Mock()
        mock_delay_service.return_value = mock_delay_instance
        
        mock_lead_processor_instance = Mock()
        mock_lead_processor.return_value = mock_lead_processor_instance
        
        mock_event_processor_instance = Mock()
        mock_event_processor_instance.validate_event = AsyncMock()
        mock_event_processor_instance.process_event = AsyncMock()
        mock_event_processor.return_value = mock_event_processor_instance
        
        # Build services
        self.container.build_services()
        
        # Verify services were registered
        assert self.container.resolve(ILeadRepository) == mock_lead_repo_instance
        assert self.container.resolve(IMessagingService) == mock_messaging_instance
        assert self.container.resolve(IAIService) == mock_ai_instance
        assert self.container.resolve(IDelayDetectionService) == mock_delay_instance

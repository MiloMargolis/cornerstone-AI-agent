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
    
    def test_register_service(self):
        """Test registering a service"""
        mock_service = Mock()
        self.container.register(ILeadRepository, mock_service)
        
        resolved_service = self.container.resolve(ILeadRepository)
        assert resolved_service == mock_service
    
    def test_register_singleton(self):
        """Test registering a singleton service"""
        mock_service = Mock()
        self.container.register_singleton(ILeadRepository, mock_service)
        
        # Resolve multiple times should return same instance
        service1 = self.container.resolve(ILeadRepository)
        service2 = self.container.resolve(ILeadRepository)
        
        assert service1 == service2
        assert service1 == mock_service
    
    def test_resolve_unregistered_service(self):
        """Test resolving an unregistered service raises error"""
        with pytest.raises(ValueError, match="No implementation registered for"):
            self.container.resolve(ILeadRepository)
    
    def test_singleton_takes_precedence(self):
        """Test that singleton takes precedence over regular registration"""
        regular_service = Mock()
        singleton_service = Mock()
        
        self.container.register(ILeadRepository, regular_service)
        self.container.register_singleton(ILeadRepository, singleton_service)
        
        resolved_service = self.container.resolve(ILeadRepository)
        assert resolved_service == singleton_service
    
    @patch.dict(os.environ, {'MOCK_TELNX': '1'})
    @patch('src.core.container.LeadRepository')
    @patch('src.core.container.MockTelnyxService')
    @patch('src.core.container.OpenAIService')
    @patch('src.core.container.DelayDetectionService')
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
        mock_event_processor_instance.validate_event = AsyncMock()  # This is called during container setup
        mock_event_processor_instance.process_event = AsyncMock()   # This is called during container setup
        mock_event_processor.return_value = mock_event_processor_instance
        
        # Build services
        self.container.build_services()
        
        # Verify services were registered
        assert self.container.resolve(ILeadRepository) == mock_lead_repo_instance
        assert self.container.resolve(IMessagingService) == mock_messaging_instance
        assert self.container.resolve(IAIService) == mock_ai_instance
        assert self.container.resolve(IDelayDetectionService) == mock_delay_instance
    
    @patch.dict(os.environ, {'MOCK_TELNX': '0'})
    @patch('src.core.container.LeadRepository')
    @patch('src.core.container.TelnyxService')
    def test_build_services_with_real_telnyx(self, mock_telnyx_service, mock_lead_repo):
        """Test building services with real Telnyx service"""
        mock_telnyx_instance = Mock()
        mock_telnyx_service.return_value = mock_telnyx_instance
        
        mock_lead_repo_instance = Mock()
        mock_lead_repo.return_value = mock_lead_repo_instance
        
        # Build services
        self.container.build_services()
        
        # Verify TelnyxService was created instead of MockTelnyxService
        mock_telnyx_service.assert_called_once()

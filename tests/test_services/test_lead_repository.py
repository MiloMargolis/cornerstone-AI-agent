import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from src.services.database.lead_repository import LeadRepository
from src.models.lead import Lead


class TestLeadRepository:
    """Test cases for LeadRepository database operations"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch.dict('os.environ', {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_KEY': 'test-key'}):
            with patch('src.services.database.lead_repository.create_client') as mock_create_client:
                # Mock the Supabase client
                mock_client = Mock()
                mock_create_client.return_value = mock_client
                
                self.repository = LeadRepository()
                
                # Store the mock client for use in tests
                self.mock_client = mock_client
    
    def test_init_missing_url(self):
        """Test initialization with missing Supabase URL"""
        with patch.dict('os.environ', {'SUPABASE_KEY': 'test-key'}, clear=True):
            with pytest.raises(ValueError, match="Missing SUPABASE_URL or SUPABASE_KEY environment variables"):
                LeadRepository()
    
    def test_init_missing_key(self):
        """Test initialization with missing Supabase key"""
        with patch.dict('os.environ', {'SUPABASE_URL': 'https://test.supabase.co'}, clear=True):
            with pytest.raises(ValueError, match="Missing SUPABASE_URL or SUPABASE_KEY environment variables"):
                LeadRepository()
    
    @pytest.mark.asyncio
    async def test_get_by_phone_success(self):
        """Test getting lead by phone number successfully"""
        phone = "+1234567890"
        lead_data = {
            "phone": phone,
            "name": "John Doe",
            "email": "john@example.com",
            "beds": "2",
            "baths": "1",
            "move_in_date": "2024-02-01",
            "price": "2000",
            "location": "Boston",
            "amenities": "Parking",
            "tour_ready": True,
            "follow_up_count": 3,
            "follow_up_stage": "final"
        }
        
        # Mock Supabase response
        mock_response = Mock()
        mock_response.data = [lead_data]
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await self.repository.get_by_phone(phone)
        
        assert result is not None
        assert result.phone == phone
        assert result.name == "John Doe"
        assert result.email == "john@example.com"
        assert result.beds == "2"
        assert result.baths == "1"
        assert result.move_in_date == "2024-02-01"
        assert result.price == "2000"
        assert result.location == "Boston"
        assert result.amenities == "Parking"
        assert result.tour_ready is True
        assert result.follow_up_count == 3
        assert result.follow_up_stage == "final"
        
        # Verify Supabase was called correctly
        self.mock_client.table.assert_called_with("leads")
        self.mock_client.table.return_value.select.assert_called_with("*")
        self.mock_client.table.return_value.select.return_value.eq.assert_called_with("phone", phone)
    
    @pytest.mark.asyncio
    async def test_get_by_phone_not_found(self):
        """Test getting lead by phone number when not found"""
        phone = "+1234567890"
        
        # Mock Supabase response with no data
        mock_response = Mock()
        mock_response.data = []
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await self.repository.get_by_phone(phone)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_phone_error(self):
        """Test getting lead by phone number when error occurs"""
        phone = "+1234567890"
        
        # Mock Supabase to raise an exception
        self.mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await self.repository.get_by_phone(phone)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_success(self):
        """Test creating a new lead successfully"""
        lead = Lead(
            phone="+1234567890",
            name="John Doe",
            email="john@example.com",
            beds="2",
            baths="1"
        )
        
        # Mock Supabase response
        mock_response = Mock()
        mock_response.data = [lead.to_dict()]
        
        self.mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        result = await self.repository.create(lead)
        
        assert result is not None
        assert result.phone == "+1234567890"
        assert result.name == "John Doe"
        assert result.email == "john@example.com"
        assert result.beds == "2"
        assert result.baths == "1"
        
        # Verify Supabase was called correctly
        self.mock_client.table.assert_called_with("leads")
        self.mock_client.table.return_value.insert.assert_called_with(lead.to_dict())
    
    @pytest.mark.asyncio
    async def test_create_error(self):
        """Test creating a lead when error occurs"""
        lead = Lead(phone="+1234567890")
        
        # Mock Supabase to raise an exception
        self.mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        result = await self.repository.create(lead)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_success(self):
        """Test updating a lead successfully"""
        phone = "+1234567890"
        updates = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "price": "2500"
        }
        
        # Mock Supabase response
        mock_response = Mock()
        mock_response.data = [{
            "phone": phone,
            "name": "Jane Doe",
            "email": "jane@example.com",
            "price": "2500"
        }]
        
        self.mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await self.repository.update(phone, updates)
        
        assert result is not None
        assert result.phone == phone
        assert result.name == "Jane Doe"
        assert result.email == "jane@example.com"
        assert result.price == "2500"
        
        # Verify Supabase was called correctly
        self.mock_client.table.assert_called_with("leads")
        self.mock_client.table.return_value.update.assert_called()
        self.mock_client.table.return_value.update.return_value.eq.assert_called_with("phone", phone)
    
    @pytest.mark.asyncio
    async def test_update_error(self):
        """Test updating a lead when error occurs"""
        phone = "+1234567890"
        updates = {"name": "Jane Doe"}
        
        # Mock Supabase to raise an exception
        self.mock_client.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        result = await self.repository.update(phone, updates)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_add_message_to_history_success(self):
        """Test adding message to history successfully"""
        phone = "+1234567890"
        message = "Hello there"
        sender = "lead"
        
        # Mock get_by_phone to return a lead
        lead = Lead(phone=phone, chat_history="Previous message")
        self.repository.get_by_phone = AsyncMock(return_value=lead)
        
        # Mock update to succeed
        self.repository.update = AsyncMock(return_value=lead)
        
        result = await self.repository.add_message_to_history(phone, message, sender)
        
        assert result is True
        
        # Verify update was called with new history
        self.repository.update.assert_called_once()
        call_args = self.repository.update.call_args
        assert call_args[0][0] == phone
        assert "chat_history" in call_args[0][1]
        assert "Hello there" in call_args[0][1]["chat_history"]
        assert "Lead:" in call_args[0][1]["chat_history"]
    
    @pytest.mark.asyncio
    async def test_add_message_to_history_lead_not_found(self):
        """Test adding message to history when lead not found"""
        phone = "+1234567890"
        message = "Hello there"
        sender = "lead"
        
        # Mock get_by_phone to return None
        self.repository.get_by_phone = AsyncMock(return_value=None)
        
        result = await self.repository.add_message_to_history(phone, message, sender)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_schedule_follow_up_success(self):
        """Test scheduling follow-up successfully"""
        phone = "+1234567890"
        days = 3
        stage = "second"
        
        # Mock update to succeed
        self.repository.update = AsyncMock(return_value=Lead(phone=phone))
        
        result = await self.repository.schedule_follow_up(phone, days, stage)
        
        assert result is True
        
        # Verify update was called with follow-up data
        self.repository.update.assert_called_once()
        call_args = self.repository.update.call_args
        assert call_args[0][0] == phone
        assert "next_follow_up_time" in call_args[0][1]
        assert "follow_up_stage" in call_args[0][1]
        assert call_args[0][1]["follow_up_stage"] == stage
    
    @pytest.mark.asyncio
    async def test_pause_follow_up_until_success(self):
        """Test pausing follow-up successfully"""
        phone = "+1234567890"
        pause_until = "2024-01-15T10:00:00"
        
        # Mock update to succeed
        self.repository.update = AsyncMock(return_value=Lead(phone=phone))
        
        result = await self.repository.pause_follow_up_until(phone, pause_until)
        
        assert result is True
        
        # Verify update was called with pause data
        self.repository.update.assert_called_once()
        call_args = self.repository.update.call_args
        assert call_args[0][0] == phone
        assert "follow_up_paused_until" in call_args[0][1]
        assert call_args[0][1]["follow_up_paused_until"] == pause_until
    
    @pytest.mark.asyncio
    async def test_set_tour_ready_success(self):
        """Test setting tour ready successfully"""
        phone = "+1234567890"
        
        # Mock update to succeed
        self.repository.update = AsyncMock(return_value=Lead(phone=phone))
        
        result = await self.repository.set_tour_ready(phone)
        
        assert result is True
        
        # Verify update was called with tour ready data
        self.repository.update.assert_called_once()
        call_args = self.repository.update.call_args
        assert call_args[0][0] == phone
        assert call_args[0][1]["tour_ready"] is True
        assert call_args[0][1]["status"] == "tour_ready"
    
    @pytest.mark.asyncio
    async def test_get_leads_needing_follow_up_success(self):
        """Test getting leads needing follow-up successfully"""
        now = datetime.now()
        lead_data = {
            "phone": "+1234567890",
            "name": "John Doe",
            "next_follow_up_time": now.isoformat(),
            "tour_ready": False,
            "follow_up_paused_until": None
        }
        
        # Mock Supabase response
        mock_response = Mock()
        mock_response.data = [lead_data]
        
        self.mock_client.table.return_value.select.return_value.not_.is_.return_value.lte.return_value.not_.is_.return_value.execute.return_value = mock_response
        
        result = await self.repository.get_leads_needing_follow_up()
        
        assert len(result) == 1
        assert result[0].phone == "+1234567890"
        assert result[0].name == "John Doe"
        
        # Verify Supabase was called correctly
        self.mock_client.table.assert_called_with("leads")
    
    @pytest.mark.asyncio
    async def test_get_leads_needing_follow_up_with_paused(self):
        """Test getting leads needing follow-up with paused follow-ups"""
        now = datetime.now()
        future_time = now + timedelta(days=1)
        
        lead_data = {
            "phone": "+1234567890",
            "name": "John Doe",
            "next_follow_up_time": now.isoformat(),
            "tour_ready": False,
            "follow_up_paused_until": future_time.isoformat()
        }
        
        # Mock Supabase response
        mock_response = Mock()
        mock_response.data = [lead_data]
        
        self.mock_client.table.return_value.select.return_value.not_.is_.return_value.lte.return_value.not_.is_.return_value.execute.return_value = mock_response
        
        result = await self.repository.get_leads_needing_follow_up()
        
        # Should filter out paused leads
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_leads_needing_follow_up_error(self):
        """Test getting leads needing follow-up when error occurs"""
        # Mock Supabase to raise an exception
        self.mock_client.table.return_value.select.return_value.not_.is_.return_value.lte.return_value.not_.is_.return_value.execute.side_effect = Exception("Database error")
        
        result = await self.repository.get_leads_needing_follow_up()
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_missing_fields(self):
        """Test getting missing required fields"""
        lead = Lead(
            phone="+1234567890",
            move_in_date="2024-02-01",
            price="2000",
            # Missing beds, baths, location, amenities
        )
        
        result = await self.repository.get_missing_fields(lead)
        
        assert "beds" in result
        assert "baths" in result
        assert "location" in result
        assert "amenities" in result
        assert "move_in_date" not in result
        assert "price" not in result
    
    @pytest.mark.asyncio
    async def test_get_missing_optional_fields(self):
        """Test getting missing optional fields"""
        lead = Lead(
            phone="+1234567890",
            # rental_urgency="High"  # REMOVED
            # Missing boston_rental_experience
        )
        
        result = await self.repository.get_missing_optional_fields(lead)
        
        assert "boston_rental_experience" in result
        # assert "rental_urgency" not in result  # REMOVED
    
    @pytest.mark.asyncio
    async def test_needs_tour_availability(self):
        """Test checking if lead needs tour availability"""
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
        
        result = await self.repository.needs_tour_availability(lead)
        
        assert result is True

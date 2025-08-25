import os
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from supabase import create_client, Client

from services.interfaces import ILeadRepository
from models.lead import Lead
from utils.constants import REQUIRED_FIELDS, OPTIONAL_FIELDS


class LeadRepository(ILeadRepository):
    """Repository implementation for lead data access using Supabase - migrated from legacy client"""

    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError(
                "Missing SUPABASE_URL or SUPABASE_KEY environment variables"
            )

        self.client: Client = create_client(url, key)

    async def get_by_phone(self, phone: str) -> Optional[Lead]:
        """Get lead by phone number"""
        try:
            response = (
                self.client.table("leads").select("*").eq("phone", phone).execute()
            )

            if response.data:
                return Lead.from_dict(response.data[0])
            return None

        except Exception as e:
            print(f"Error getting lead by phone: {e}")
            return None

    async def create(self, lead: Lead) -> Optional[Lead]:
        """Create a new lead"""
        try:
            lead_data = lead.to_dict()
            response = self.client.table("leads").insert(lead_data).execute()

            if response.data:
                return Lead.from_dict(response.data[0])
            return None

        except Exception as e:
            print(f"Error creating lead: {e}")
            return None

    async def update(self, phone: str, updates: Dict[str, Any]) -> Optional[Lead]:
        """Update lead with new information"""
        try:
            # Always update last_contacted timestamp
            updates["last_contacted"] = "now()"

            response = (
                self.client.table("leads").update(updates).eq("phone", phone).execute()
            )

            if response.data:
                return Lead.from_dict(response.data[0])
            return None

        except Exception as e:
            print(f"Error updating lead: {e}")
            return None

    async def add_message_to_history(
        self, phone: str, message: str, sender: str
    ) -> bool:
        """Add message to lead's chat history"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            message_entry = f"{timestamp} - {sender.title()}: {message}\n"

            # Get current chat history
            lead = await self.get_by_phone(phone)
            if not lead:
                return False

            current_history = lead.chat_history or ""
            new_history = current_history + message_entry

            # Update with new history
            await self.update(phone, {"chat_history": new_history})
            return True

        except Exception as e:
            print(f"Error adding message to history: {e}")
            return False

    async def schedule_follow_up(self, phone: str, days: int, stage: str) -> bool:
        """Schedule a follow-up for a lead"""
        try:
            next_follow_up = datetime.now() + timedelta(days=days)

            await self.update(
                phone,
                {
                    "next_follow_up_time": next_follow_up.isoformat(),
                    "follow_up_stage": stage,
                },
            )
            return True

        except Exception as e:
            print(f"Error scheduling follow-up: {e}")
            return False

    async def pause_follow_up_until(self, phone: str, pause_until: str) -> bool:
        """Pause follow-ups until specified time"""
        try:
            await self.update(phone, {"follow_up_paused_until": pause_until})
            return True

        except Exception as e:
            print(f"Error pausing follow-up: {e}")
            return False

    async def set_tour_ready(self, phone: str) -> bool:
        """Mark lead as tour ready"""
        try:
            await self.update(phone, {"tour_ready": True, "status": "tour_ready"})
            return True

        except Exception as e:
            print(f"Error setting tour ready: {e}")
            return False

    async def get_leads_needing_follow_up(self) -> List[Lead]:
        """Get leads that need follow-up messages"""
        try:
            now = datetime.now()

            response = (
                self.client.table("leads")
                .select("*")
                .not_.is_("next_follow_up_time", "null")
                .lte("next_follow_up_time", now.isoformat())
                .not_.is_("tour_ready", "true")
                .execute()
            )

            leads = []
            for lead_data in response.data:
                # Check if follow-up is paused
                paused_until = lead_data.get("follow_up_paused_until")
                if paused_until:
                    try:
                        paused_until_dt = datetime.fromisoformat(
                            paused_until.replace("Z", "+00:00")
                        )
                        if now < paused_until_dt:
                            continue
                    except:
                        pass

                leads.append(Lead.from_dict(lead_data))

            return leads

        except Exception as e:
            print(f"Error getting leads needing follow-up: {e}")
            return []

    async def get_missing_fields(self, lead: Lead) -> List[str]:
        """Get list of missing required fields for a lead"""
        return lead.missing_required_fields

    async def get_missing_optional_fields(self, lead: Lead) -> List[str]:
        """Get list of missing optional fields for a lead"""
        return lead.missing_optional_fields

    async def needs_tour_availability(self, lead: Lead) -> bool:
        """Check if lead needs tour availability information"""
        return lead.needs_tour_availability

import os
from supabase import create_client, Client
from typing import Dict, Optional, List
import json
from datetime import datetime, timedelta

class SupabaseClient:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        self.client: Client = create_client(url, key)
        try:
            assert self.client is not None, "Supabase client creation failed"
            # Try a simple query to check connection (e.g., list tables or select from a known table)
            self.client.table("leads").select("*").limit(1).execute()
        except Exception as e:
            raise RuntimeError(f"Supabase client creation or test query failed: {e}")
    
    def get_lead_by_phone(self, phone: str) -> Optional[Dict]:
        """Get lead record by phone number"""
        try:
            response = self.client.table("leads").select("*").eq("phone", phone).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting lead by phone: {e}") ## TODO: Should this really be an error? It seems like we are just checking if lead is present or not, not an error to create new lead.
            return None
    
    def create_lead(self, phone: str, initial_message: str = "") -> Optional[Dict]:
        """Create a new lead record"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            initial_chat = f"{timestamp} - Lead: {initial_message}\n" if initial_message else ""
            
            lead_data = {
                "phone": phone,
                "name": "",
                "email": "",
                "beds": "",
                "baths": "",
                "move_in_date": "",
                "price": "",
                "location": "",
                "amenities": "",
                "tour_availability": "",
                "tour_ready": False,
                "chat_history": initial_chat,
                "follow_up_count": 0,
                "next_follow_up_time": None,
                "follow_up_paused_until": None,
                "follow_up_stage": "scheduled"
            }
            response = self.client.table("leads").insert(lead_data).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error creating lead: {e}")
            return None
    
    def update_lead(self, phone: str, updates: Dict) -> Optional[Dict]:
        """Update lead record with new information"""
        try:
            # Always update last_contacted timestamp
            updates["last_contacted"] = "now()"
            
            response = self.client.table("leads").update(updates).eq("phone", phone).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error updating lead: {e}")
            return None
    
    def get_missing_fields(self, lead: Dict) -> List[str]:
        """Get list of qualification fields that are still empty for a lead"""
        qualification_fields = ["move_in_date", "price", "beds", "baths", "location", "amenities"]
        missing_fields = []
        
        for field in qualification_fields:
            if not lead.get(field) or lead.get(field).strip() == "":
                missing_fields.append(field)
        
        return missing_fields
    
    def is_qualification_complete(self, lead: Dict) -> bool:
        """Check if all qualification fields are complete"""
        return len(self.get_missing_fields(lead)) == 0
    
    def needs_tour_availability(self, lead: Dict) -> bool:
        """Check if tour availability is needed"""
        return (self.is_qualification_complete(lead) and 
                (not lead.get("tour_availability") or lead.get("tour_availability").strip() == "") and
                not lead.get("tour_ready", False))
    
    def set_tour_ready(self, phone: str) -> bool:
        """Mark lead as tour ready"""
        try:
            updates = {
                "tour_ready": True,
                "last_contacted": "now()"
            }
            result = self.update_lead(phone, updates)
            return result is not None
        except Exception as e:
            print(f"Error setting tour ready: {e}")
            return False
    
    def add_message_to_history(self, phone: str, message: str, sender: str = "lead"):
        """Add a message to the lead's conversation history"""
        try:
            from datetime import datetime
            lead = self.get_lead_by_phone(phone)
            if lead:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                existing_history = lead.get("chat_history", "")
                sender_label = "Lead" if sender == "lead" else "AI"
                new_entry = f"{timestamp} - {sender_label}: {message}\n"
                
                updated_history = existing_history + new_entry
                
                updates = {
                    "chat_history": updated_history,
                    "last_contacted": "now()"
                }
                self.update_lead(phone, updates)
        except Exception as e:
            print(f"Error adding message to history: {e}")
    
    def schedule_follow_up(self, phone: str, days: int, stage: str) -> bool:
        """Schedule next follow-up for a lead"""
        try:
            from datetime import datetime, timedelta
            next_follow_up = datetime.now() + timedelta(days=days)
            
            updates = {
                "next_follow_up_time": next_follow_up.isoformat(),
                "follow_up_stage": stage
            }
            
            result = self.update_lead(phone, updates)
            return result is not None
        except Exception as e:
            print(f"Error scheduling follow-up: {e}")
            return False
    
    def pause_follow_up_until(self, phone: str, until_date: datetime) -> bool:
        """Pause follow-ups until a specific date"""
        try:
            updates = {
                "follow_up_paused_until": until_date.isoformat(),
                "next_follow_up_time": None  # Clear any scheduled follow-up
            }
            
            result = self.update_lead(phone, updates)
            return result is not None
        except Exception as e:
            print(f"Error pausing follow-up: {e}")
            return False
    
    def get_leads_needing_follow_up(self) -> List[Dict]:
        """Get leads that need follow-up messages"""
        try:
            current_time = datetime.now()
            
            # Query for leads that:
            # - Are not tour_ready
            # - Have qualification missing
            # - Have next_follow_up_time <= now
            # - Are not paused or pause period has expired
            # - Haven't exceeded max follow-ups
            
            response = self.client.table("leads").select("*").execute()
            
            leads_to_follow_up = []
            for lead in response.data:
                # Skip if tour ready
                if lead.get("tour_ready", False):
                    continue
                
                # Skip if all qualification fields are complete
                if len(self.get_missing_fields(lead)) == 0:
                    continue
                
                # Skip if max follow-ups exceeded
                if lead.get("follow_up_count", 0) >= 5:  # MAX_FOLLOW_UPS
                    continue
                
                # Skip if paused and pause period hasn't expired
                if lead.get("follow_up_paused_until"):
                    pause_until = datetime.fromisoformat(lead["follow_up_paused_until"].replace("Z", "+00:00"))
                    if current_time < pause_until:
                        continue
                
                # Include if next_follow_up_time is due
                if lead.get("next_follow_up_time"):
                    follow_up_time = datetime.fromisoformat(lead["next_follow_up_time"].replace("Z", "+00:00"))
                    if current_time >= follow_up_time:
                        leads_to_follow_up.append(lead)
            
            return leads_to_follow_up
        except Exception as e:
            print(f"Error getting leads for follow-up: {e}")
            return []
    
    def increment_follow_up_count(self, phone: str) -> bool:
        """Increment follow-up count for a lead"""
        try:
            lead = self.get_lead_by_phone(phone)
            if lead:
                new_count = lead.get("follow_up_count", 0) + 1
                updates = {
                    "follow_up_count": new_count,
                    "next_follow_up_time": None  # Clear this follow-up
                }
                result = self.update_lead(phone, updates)
                return result is not None
            return False
        except Exception as e:
            print(f"Error incrementing follow-up count: {e}")
            return False 
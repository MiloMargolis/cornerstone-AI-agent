import os
from supabase import create_client, Client
from typing import Dict, Optional, List
import json

class SupabaseClient:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        self.client: Client = create_client(url, key)
    
    def get_lead_by_phone(self, phone: str) -> Optional[Dict]:
        """Get lead record by phone number"""
        try:
            response = self.client.table("leads").select("*").eq("phone", phone).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting lead by phone: {e}")
            return None
    
    def create_lead(self, phone: str, initial_message: str = "") -> Optional[Dict]:
        """Create a new lead record"""
        try:
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
                "other_notes": initial_message
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
        """Get list of fields that are still empty for a lead"""
        required_fields = ["name", "move_in_date", "price", "beds", "baths", "location", "amenities"]
        missing_fields = []
        
        for field in required_fields:
            if not lead.get(field) or lead.get(field).strip() == "":
                missing_fields.append(field)
        
        return missing_fields
    
    def add_message_to_history(self, phone: str, message: str, sender: str = "lead"):
        """Add a message to the lead's conversation history"""
        try:
            lead = self.get_lead_by_phone(phone)
            if lead:
                # For now, just update the other_notes field with the latest message
                # In the future, we might want a separate messages table
                updates = {
                    "other_notes": message,
                    "last_contacted": "now()"
                }
                self.update_lead(phone, updates)
        except Exception as e:
            print(f"Error adding message to history: {e}") 
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
                "chat_history": initial_chat
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
                (not lead.get("tour_availability") or lead.get("tour_availability").strip() == ""))
    
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
import os
import json
from typing import Dict, List, Optional
from google.auth.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetsClient:
    def __init__(self):
        """Initialize Google Sheets client with service account credentials"""
        try:
            # Get credentials from environment variable (JSON string)
            creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
            if not creds_json:
                print("Warning: GOOGLE_SHEETS_CREDENTIALS_JSON not found - Google Sheets sync disabled")
                self.enabled = False
                return
            
            # Parse credentials JSON
            creds_info = json.loads(creds_json)
            
            # Set up credentials with required scopes
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=credentials)
            self.sheet_id = os.getenv("GOOGLE_SHEETS_SHEET_ID")
            
            if not self.sheet_id:
                print("Warning: GOOGLE_SHEETS_SHEET_ID not found - Google Sheets sync disabled")
                self.enabled = False
                return
            
            self.enabled = True
            print(f"Google Sheets client initialized successfully for sheet: {self.sheet_id}")
            
        except Exception as e:
            print(f"Error initializing Google Sheets client: {e}")
            self.enabled = False
    
    def sync_lead_data(self, lead_data: Dict) -> bool:
        """Sync lead data to Google Sheets"""
        if not self.enabled:
            return False
        
        try:
            # Define the columns we want to sync (in order)
            columns = [
                'phone', 'name', 'email', 'beds', 'baths', 
                'move_in_date', 'price', 'location', 'amenities',
                'tour_availability', 'tour_ready', 'date_connected', 'last_contacted'
            ]
            
            # Convert lead data to row format
            row_data = []
            for col in columns:
                value = lead_data.get(col, '')
                # Convert boolean values to readable text
                if isinstance(value, bool):
                    value = 'Yes' if value else 'No'
                # Convert None to empty string
                if value is None:
                    value = ''
                row_data.append(str(value))
            
            # Check if lead already exists in sheet
            phone = lead_data.get('phone', '')
            existing_row = self._find_lead_row(phone)
            
            if existing_row:
                # Update existing row
                self._update_row(existing_row, row_data)
                print(f"[SHEETS] Updated lead {phone} in row {existing_row}")
            else:
                # Add new row
                self._add_row(row_data)
                print(f"[SHEETS] Added new lead {phone} to sheet")
            
            return True
            
        except Exception as e:
            print(f"[SHEETS] Error syncing lead data for {lead_data.get('phone', 'unknown')}: {e}")
            return False
    
    def _ensure_headers(self) -> bool:
        """Ensure the sheet has proper headers"""
        try:
            headers = [
                'Phone', 'Name', 'Email', 'Bedrooms', 'Bathrooms',
                'Move-in Date', 'Price Range', 'Location', 'Amenities',
                'Tour Availability', 'Tour Ready', 'Date Connected', 'Last Contacted'
            ]
            
            # Check if headers exist
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='A1:M1'
            ).execute()
            
            existing_headers = result.get('values', [[]])
            
            if not existing_headers or existing_headers[0] != headers:
                # Add or update headers
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range='A1:M1',
                    valueInputOption='RAW',
                    body={'values': [headers]}
                ).execute()
                print("[SHEETS] Headers added/updated")
            
            return True
            
        except Exception as e:
            print(f"[SHEETS] Error ensuring headers: {e}")
            return False
    
    def _find_lead_row(self, phone: str) -> Optional[int]:
        """Find the row number for a lead by phone number"""
        try:
            # Get all phone numbers (column A)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='A:A'
            ).execute()
            
            values = result.get('values', [])
            
            for i, row in enumerate(values):
                if row and len(row) > 0 and row[0] == phone:
                    return i + 1  # Sheets are 1-indexed
            
            return None
            
        except Exception as e:
            print(f"[SHEETS] Error finding lead row for {phone}: {e}")
            return None
    
    def _update_row(self, row_number: int, row_data: List) -> bool:
        """Update an existing row with new data"""
        try:
            range_name = f'A{row_number}:M{row_number}'
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [row_data]}
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"[SHEETS] Error updating row {row_number}: {e}")
            return False
    
    def _add_row(self, row_data: List) -> bool:
        """Add a new row to the sheet"""
        try:
            # Ensure headers exist first
            self._ensure_headers()
            
            # Append the new row
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range='A:M',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [row_data]}
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"[SHEETS] Error adding new row: {e}")
            return False 
#!/usr/bin/env python3
"""Google Calendar Sync via OAuth2 - Uses existing Google client credentials."""

import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pickle

class GoogleCalendarSyncOAuth:
    """Sync to Google Calendar using OAuth2 (already configured in OpenClaw)."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, scout_email: str = "jeffriesr27@darden.virginia.edu"):
        self.scout_email = scout_email
        self.creds_file = Path.home() / ".openclaw/credentials/google-client-secret.json"
        self.token_file = Path.home() / ".openclaw/workspace/integrations/kanban/google_token.pickle"
        self.event_tracking = {}
        self.credentials = self._load_credentials()
    
    def _load_credentials(self):
        """Load or create Google OAuth credentials."""
        # Try to load cached token
        if self.token_file.exists():
            with open(self.token_file, 'rb') as f:
                creds = pickle.load(f)
                # Refresh if needed
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self._save_credentials(creds)
                return creds
        
        # Create new flow from client secret
        if not self.creds_file.exists():
            return None
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.creds_file),
                self.SCOPES
            )
            # For server auth, use authorization_url
            auth_url, state = flow.authorization_url(prompt='consent')
            print(f"\n🔗 Authorize Google Calendar access:\n{auth_url}\n")
            # In production, handle callback
            return None
        except Exception as e:
            print(f"Google Calendar auth error: {e}")
            return None
    
    def _save_credentials(self, creds):
        """Save credentials to disk."""
        with open(self.token_file, 'wb') as f:
            pickle.dump(creds, f)
    
    def _get_service(self):
        """Get Google Calendar API service."""
        if not self.credentials:
            return None
        
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        
        try:
            service = build('calendar', 'v3', credentials=self.credentials)
            return service
        except Exception as e:
            print(f"Google Calendar service error: {e}")
            return None
    
    def add_event(self, item, user: str) -> dict:
        """Add event to Google Calendar."""
        service = self._get_service()
        if not service:
            return {"error": "Google Calendar not authenticated"}
        
        try:
            due_date = datetime.fromisoformat(item.due_date)
        except:
            return {"error": "Invalid due_date"}
        
        event = {
            "summary": f"[TDL-{item.priority.name}] {item.title}",
            "description": f"Task ID: {item.id}\nPriority: {item.priority.name}\nStatus: {item.status.value}\n{item.description}",
            "start": {
                "dateTime": f"{item.due_date}T09:00:00",
                "timeZone": "America/New_York"
            },
            "end": {
                "dateTime": f"{item.due_date}T10:00:00",
                "timeZone": "America/New_York"
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 1440},  # 24 hours
                    {"method": "popup", "minutes": 15}
                ]
            }
        }
        
        try:
            event_result = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            self.event_tracking[item.id] = event_result.get('id')
            return event_result
        except Exception as e:
            return {"error": f"Failed to create Google Calendar event: {str(e)}"}
    
    def update_event(self, item, user: str) -> dict:
        """Update event in Google Calendar."""
        service = self._get_service()
        if not service or item.id not in self.event_tracking:
            return {"message": "Event update skipped"}
        
        event_id = self.event_tracking[item.id]
        
        try:
            due_date = datetime.fromisoformat(item.due_date)
        except:
            return {"error": "Invalid due_date"}
        
        update_data = {
            "summary": f"[TDL-{item.priority.name}] {item.title}",
            "description": f"Task ID: {item.id}\nPriority: {item.priority.name}\nStatus: {item.status.value}\n{item.description}",
            "start": {
                "dateTime": f"{item.due_date}T09:00:00",
                "timeZone": "America/New_York"
            },
            "end": {
                "dateTime": f"{item.due_date}T10:00:00",
                "timeZone": "America/New_York"
            }
        }
        
        try:
            service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=update_data
            ).execute()
            return {"ok": True}
        except Exception as e:
            return {"error": f"Failed to update Google Calendar event: {str(e)}"}
    
    def remove_event(self, item_id: str) -> dict:
        """Remove event from Google Calendar."""
        service = self._get_service()
        if not service or item_id not in self.event_tracking:
            return {"message": "Event removal skipped"}
        
        event_id = self.event_tracking[item_id]
        
        try:
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            del self.event_tracking[item_id]
            return {"ok": True}
        except Exception as e:
            return {"error": f"Failed to remove Google Calendar event: {str(e)}"}

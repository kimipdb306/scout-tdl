#!/usr/bin/env python3
"""Outlook Calendar Sync via Microsoft Graph API."""

import requests
from datetime import datetime, timedelta
import json
from pathlib import Path

class OutlookCalendarSync:
    def __init__(self, scout_email: str = "jeffriesr27@darden.virginia.edu"):
        self.scout_email = scout_email
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self.event_tracking = {}  # item_id -> event_id mapping
        self.token = None
    
    def set_token(self, access_token: str):
        """Set the access token for API calls."""
        self.token = access_token
    
    def _get_headers(self) -> dict:
        """Get headers for API calls."""
        if not self.token:
            return {}
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def add_event(self, item, user: str) -> dict:
        """Add event to Outlook calendar."""
        if not self.token:
            return {"error": "Not authenticated. Please sign in to Outlook first."}
        
        try:
            due_date = datetime.fromisoformat(item.due_date)
        except:
            return {"error": "Invalid due_date"}
        
        # Create all-day event (or use specific time)
        event = {
            "subject": f"[TDL-{item.priority.name}] {item.title}",
            "start": {
                "dateTime": f"{item.due_date}T09:00:00",
                "timeZone": "Eastern Standard Time"
            },
            "end": {
                "dateTime": f"{item.due_date}T10:00:00",
                "timeZone": "Eastern Standard Time"
            },
            "body": {
                "contentType": "HTML",
                "content": f"<p><b>Task ID:</b> {item.id}</p><p><b>Priority:</b> {item.priority.name}</p><p><b>Status:</b> {item.status.value}</p><p>{item.description}</p>"
            },
            "categories": ["TDL", item.priority.name],
            "isReminderOn": True,
            "reminderMinutesBeforeStart": 1440,  # 24 hours before
        }
        
        try:
            resp = requests.post(
                f"{self.graph_endpoint}/me/events",
                headers=self._get_headers(),
                json=event,
                timeout=10
            )
            
            if resp.status_code == 201:
                event_data = resp.json()
                self.event_tracking[item.id] = event_data.get("id")
                return event_data
            else:
                return {"error": f"Outlook API error: {resp.status_code} - {resp.text}"}
        except Exception as e:
            return {"error": f"Failed to create Outlook event: {str(e)}"}
    
    def update_event(self, item, user: str) -> dict:
        """Update event in Outlook calendar."""
        if not self.token or item.id not in self.event_tracking:
            return {"message": "Event update skipped (not tracked)"}
        
        event_id = self.event_tracking[item.id]
        
        try:
            due_date = datetime.fromisoformat(item.due_date)
        except:
            return {"error": "Invalid due_date"}
        
        update_data = {
            "subject": f"[TDL-{item.priority.name}] {item.title}",
            "start": {
                "dateTime": f"{item.due_date}T09:00:00",
                "timeZone": "Eastern Standard Time"
            },
            "end": {
                "dateTime": f"{item.due_date}T10:00:00",
                "timeZone": "Eastern Standard Time"
            },
            "body": {
                "contentType": "HTML",
                "content": f"<p><b>Task ID:</b> {item.id}</p><p><b>Priority:</b> {item.priority.name}</p><p><b>Status:</b> {item.status.value}</p><p>{item.description}</p>"
            }
        }
        
        try:
            resp = requests.patch(
                f"{self.graph_endpoint}/me/events/{event_id}",
                headers=self._get_headers(),
                json=update_data,
                timeout=10
            )
            
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"error": f"Outlook API error: {resp.status_code}"}
        except Exception as e:
            return {"error": f"Failed to update Outlook event: {str(e)}"}
    
    def remove_event(self, item_id: str) -> dict:
        """Remove event from Outlook calendar."""
        if not self.token or item_id not in self.event_tracking:
            return {"message": "Event removal skipped (not tracked)"}
        
        event_id = self.event_tracking[item_id]
        
        try:
            resp = requests.delete(
                f"{self.graph_endpoint}/me/events/{event_id}",
                headers=self._get_headers(),
                timeout=10
            )
            
            if resp.status_code == 204:
                del self.event_tracking[item_id]
                return {"ok": True}
            else:
                return {"error": f"Outlook API error: {resp.status_code}"}
        except Exception as e:
            return {"error": f"Failed to remove Outlook event: {str(e)}"}

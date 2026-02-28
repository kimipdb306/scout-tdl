#!/usr/bin/env python3
"""Google Calendar Sync via gog CLI."""

import subprocess
import json
from datetime import datetime, timedelta

class GoogleCalendarSync:
    def __init__(self, scout_email: str, scout_alt_email: str):
        self.scout_email = scout_email
        self.scout_alt_email = scout_alt_email
        self.event_tracking = {}  # Track item_id -> event_id mappings
    
    def _get_email_for_user(self, user: str) -> str:
        """Get email address for user."""
        if user == "scout":
            return self.scout_email
        elif user == "reid":
            return self.scout_alt_email  # Reid can use alt email or his own
        return None
    
    def _run_gog(self, args: list) -> dict:
        """Run gog CLI command and return JSON result."""
        try:
            result = subprocess.run(
                ["gog"] + args + ["--json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return json.loads(result.stdout) if result.stdout else {}
            else:
                print(f"gog error: {result.stderr}")
                return {}
        except Exception as e:
            print(f"gog exception: {e}")
            return {}
    
    def add_event(self, item, user: str) -> dict:
        """Add event to Google Calendar."""
        email = self._get_email_for_user(user)
        if not email:
            return {"error": f"No email for user {user}"}
        
        # Parse due date
        try:
            due_date = datetime.fromisoformat(item.due_date)
            start_time = due_date.isoformat()
            end_time = (due_date + timedelta(hours=1)).isoformat()
        except:
            return {"error": "Invalid due_date"}
        
        event_summary = f"[TDL-{item.priority.name}] {item.title}"
        
        # Use gog to create calendar event
        args = [
            "calendar", "create",
            "--summary", event_summary,
            "--start", start_time,
            "--end", end_time,
            "--description", f"Task ID: {item.id}\nPriority: {item.priority.name}\n{item.description}",
            "--calendar", "calendar",  # Default calendar
            "--account", email
        ]
        
        result = self._run_gog(args)
        if result:
            self.event_tracking[item.id] = result.get("id", item.id)
        return result
    
    def update_event(self, item, user: str) -> dict:
        """Update event in Google Calendar."""
        email = self._get_email_for_user(user)
        if not email:
            return {"error": f"No email for user {user}"}
        
        event_id = self.event_tracking.get(item.id, item.id)
        
        try:
            due_date = datetime.fromisoformat(item.due_date)
            start_time = due_date.isoformat()
            end_time = (due_date + timedelta(hours=1)).isoformat()
        except:
            return {"error": "Invalid due_date"}
        
        event_summary = f"[TDL-{item.priority.name}] {item.title}"
        
        args = [
            "calendar", "update",
            event_id,
            "--summary", event_summary,
            "--start", start_time,
            "--end", end_time,
            "--account", email
        ]
        
        return self._run_gog(args)
    
    def remove_event(self, item_id: str) -> dict:
        """Remove event from Google Calendar."""
        event_id = self.event_tracking.get(item_id, item_id)
        
        args = [
            "calendar", "delete",
            event_id
        ]
        
        result = self._run_gog(args)
        if result:
            del self.event_tracking[item_id]
        return result

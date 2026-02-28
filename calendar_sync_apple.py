#!/usr/bin/env python3
"""Apple Calendar Sync via local Calendar app or iCloud."""

import subprocess
import json
from datetime import datetime, timedelta

class AppleCalendarSync:
    def __init__(self):
        self.event_tracking = {}
    
    def add_event(self, item, user: str) -> dict:
        """Add event to Apple Calendar via osascript."""
        try:
            due_date = datetime.fromisoformat(item.due_date)
        except:
            return {"error": "Invalid due_date"}
        
        # Build AppleScript command
        title = f"[TDL-{item.priority.name}] {item.title}"
        notes = f"Task ID: {item.id}\nPriority: {item.priority.name}\nStatus: {item.status.value}\n{item.description}"
        
        script = f'''
        tell application "Calendar"
            create event with properties {{
                summary: "{title}",
                start date: (date "{due_date.strftime('%A, %B %d, %Y at %I:%M %p')}"),
                end date: (date "{(due_date + timedelta(hours=1)).strftime('%A, %B %d, %Y at %I:%M %p')}"),
                description: "{notes}",
                allday event: false
            }}
        end tell
        '''
        
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.event_tracking[item.id] = True
                return {"ok": True, "calendar": "Apple"}
            else:
                return {"error": f"Apple Calendar error: {result.stderr}"}
        except Exception as e:
            return {"error": f"Failed to add to Apple Calendar: {str(e)}"}
    
    def update_event(self, item, user: str) -> dict:
        """Update event in Apple Calendar."""
        # AppleScript doesn't provide easy event ID retrieval
        # For MVP, we'll remove and re-add
        self.remove_event(item.id)
        return self.add_event(item, user)
    
    def remove_event(self, item_id: str) -> dict:
        """Remove event from Apple Calendar."""
        # This would require more complex AppleScript
        # For MVP, events stay but can be manually deleted
        return {"message": "Apple Calendar event removal requires manual deletion"}

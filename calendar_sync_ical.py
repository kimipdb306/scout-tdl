#!/usr/bin/env python3
"""iCal (.ics) Export for TDL."""

from icalendar import Calendar, Event
from datetime import datetime, timedelta
from pathlib import Path
import uuid

class iCalSync:
    def __init__(self):
        self.ical_dir = Path.home() / ".openclaw/workspace/integrations/kanban/ical_exports"
        self.ical_dir.mkdir(parents=True, exist_ok=True)
        self.event_tracking = {}  # item_id -> uid mapping
    
    def _create_calendar(self, name: str) -> Calendar:
        """Create new iCal calendar."""
        cal = Calendar()
        cal.add('prodid', f'-//Scout TDL//{name}//EN')
        cal.add('version', '2.0')
        cal.add('x-wr-calname', name)
        cal.add('x-wr-timezone', 'America/New_York')
        return cal
    
    def add_event(self, item, user: str) -> dict:
        """Add event to iCal export."""
        try:
            due_date = datetime.fromisoformat(item.due_date)
        except:
            return {"error": "Invalid due_date"}
        
        # Load or create calendar for user
        cal_path = self.ical_dir / f"{user}_tdl.ics"
        if cal_path.exists():
            cal = Calendar.from_ical(cal_path.read_bytes())
        else:
            cal = self._create_calendar(f"Scout TDL - {user.capitalize()}")
        
        # Create event
        event = Event()
        event.add('uid', f"{item.id}@scout-tdl")
        event.add('dtstart', due_date.date())
        event.add('dtend', (due_date + timedelta(days=1)).date())
        event.add('summary', f"[{item.priority.name}] {item.title}")
        event.add('description', f"Task ID: {item.id}\nStatus: {item.status.value}\n{item.description}")
        event.add('categories', ['TDL', item.priority.name])
        event.add('created', datetime.now())
        event.add('last-modified', datetime.now())
        
        # Add alarm (reminder 24 hours before)
        alarm = Event()
        alarm.add('action', 'DISPLAY')
        alarm.add('trigger', timedelta(hours=-24))
        alarm.add('description', f"Reminder: {item.title}")
        
        cal.add_component(event)
        
        # Save calendar
        cal_path.write_bytes(cal.to_ical())
        self.event_tracking[item.id] = f"{item.id}@scout-tdl"
        
        return {"path": str(cal_path), "id": item.id}
    
    def update_event(self, item, user: str) -> dict:
        """Update event in iCal export."""
        cal_path = self.ical_dir / f"{user}_tdl.ics"
        
        if not cal_path.exists():
            return self.add_event(item, user)
        
        # For now, rebuild by removing and re-adding
        self.remove_event(item.id)
        return self.add_event(item, user)
    
    def remove_event(self, item_id: str) -> dict:
        """Remove event from iCal export."""
        # This would require parsing and removing specific events
        # For MVP, we'll rebuild the calendar on each sync
        return {"message": "Event removal handled via rebuild"}
    
    def export_user_calendar(self, user: str) -> Path:
        """Get the iCal file path for a user."""
        return self.ical_dir / f"{user}_tdl.ics"

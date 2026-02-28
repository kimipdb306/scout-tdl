#!/usr/bin/env python3
"""Sync kanban items to Google Calendar, Teams, and iCal."""

import json
from pathlib import Path
from datetime import datetime
from typing import List
import subprocess

from kanban_db import KanbanBoard, KanbanItem

ICAL_FILE = Path.home() / ".openclaw/workspace/kanban.ics"


def sync_to_google_calendar(items: List[KanbanItem]):
    """Sync items with due dates to Google Calendar using gog."""
    for item in items:
        if not item.due_date:
            continue

        # Parse due date
        from datetime import datetime as dt
        due = dt.fromisoformat(item.due_date)
        iso_start = due.isoformat()
        iso_end = (due.replace(hour=23, minute=59)).isoformat()

        # Create calendar event via gog
        event_title = f"[{item.priority.name}] {item.title}"
        event_desc = f"Status: {item.status.value}\n{item.description}"

        cmd = [
            "gog", "calendar", "create", "primary",
            "--summary", event_title,
            "--description", event_desc,
            "--from", iso_start,
            "--to", iso_end,
            "--account", "kimipdb@gmail.com"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Synced '{item.title}' to Google Calendar")
        else:
            print(f"✗ Failed to sync '{item.title}': {result.stderr}")


def sync_to_ical(items: List[KanbanItem]):
    """Generate iCal file with kanban items."""
    ical_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Scout Kanban//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Scout Kanban",
        "X-WR-TIMEZONE:America/New_York",
    ]

    for item in items:
        if not item.due_date:
            continue

        # Generate unique UID
        uid = f"{item.id}@scoutkanban"
        created = item.created_at.replace(":", "").replace("-", "")[:15]
        dtstamp = datetime.now().isoformat().replace(":", "").replace("-", "")[:15]

        ical_lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}Z",
            f"CREATED:{created}Z",
            f"SUMMARY:[{item.priority.name}] {item.title}",
            f"DESCRIPTION:Status: {item.status.value}\\n{item.description}",
            f"DTSTART;VALUE=DATE:{item.due_date.replace('-', '')}",
            f"DTEND;VALUE=DATE:{item.due_date.replace('-', '')}",
            "END:VEVENT",
        ])

    ical_lines.append("END:VCALENDAR")
    ical_content = "\r\n".join(ical_lines)
    ICAL_FILE.write_text(ical_content)
    print(f"✓ Generated iCal file at {ICAL_FILE}")
    print(f"  Subscribe via: webcal://localhost:8000/kanban.ics")


def sync_to_teams():
    """Sync to Teams (requires Teams API setup - placeholder)."""
    # Would require Teams app registration and OAuth
    # For now, manual: export as CSV and use Teams integration
    print("⚠ Teams sync requires manual setup (Teams API)")
    print("  Export kanban data as CSV and import to Teams tasks")


def sync_all():
    """Sync kanban to all calendars."""
    board = KanbanBoard()

    print("Syncing kanban to calendars...")
    sync_to_google_calendar(board.items)
    sync_to_ical(board.items)
    sync_to_teams()
    print("\n✓ Sync complete")


if __name__ == "__main__":
    sync_all()

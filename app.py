#!/usr/bin/env python3
"""Scout TDL - Automatic Calendar Sync Edition
Every task change automatically syncs to Outlook, Google, Apple, and iCal.
No manual buttons needed.
"""

from flask import Flask, render_template, request, jsonify
from kanban_db import KanbanBoard, Status, Priority
from calendar_sync_outlook import OutlookCalendarSync
from calendar_sync_google import GoogleCalendarSync
from calendar_sync_apple import AppleCalendarSync
from calendar_sync_ical import iCalSync
from calendar_sync_auto import AutoCalendarSync
import json
from pathlib import Path
import os
from datetime import datetime

_app_dir = Path(__file__).parent
app = Flask(__name__, template_folder=str(_app_dir / "templates"), static_folder=str(_app_dir / "static"))
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# User boards
boards = {
    "scout": KanbanBoard("scout"),
    "reid": KanbanBoard("reid")
}

# Initialize calendar sync services
outlook_sync = OutlookCalendarSync(
    scout_email=os.environ.get("SCOUT_EMAIL", "jeffriesr27@darden.virginia.edu")
)
google_sync = GoogleCalendarSync(
    scout_email=os.environ.get("SCOUT_EMAIL", "jeffriesr27@darden.virginia.edu"),
    scout_alt_email=os.environ.get("SCOUT_ALT_EMAIL", "dsn9zx@darden.virginia.edu")
)
apple_sync = AppleCalendarSync()
ical_sync = iCalSync()

# Auto-sync service (syncs to all calendars automatically)
auto_sync = AutoCalendarSync(
    outlook_sync=outlook_sync,
    google_sync=google_sync,
    apple_sync=apple_sync,
    ical_sync=ical_sync
)
auto_sync.enable_auto_sync()

# Routes
@app.route("/")
def index():
    """Serve kanban board UI."""
    return render_template("index.html")

# Multi-user API endpoints with AUTOMATIC SYNC
@app.route("/api/<user>/items", methods=["GET"])
def get_items(user):
    """Get all items for a user grouped by status."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        status.value: [
            item.to_dict() for item in board.get_items_by_status(status)
        ]
        for status in Status
    })

@app.route("/api/<user>/items", methods=["POST"])
def create_item(user):
    """Create new item for user - AUTO-SYNCS to all calendars."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    item = board.add_item(
        title=data.get("title"),
        priority=Priority[data.get("priority", "MEDIUM")],
        due_date=data.get("due_date"),
        description=data.get("description", "")
    )
    
    # AUTO-SYNC: Send to all calendars in background
    if item.due_date:
        auto_sync.add_item_to_all_calendars(item, user)
    
    return jsonify(item.to_dict()), 201

@app.route("/api/<user>/items/<item_id>", methods=["GET"])
def get_item(user, item_id):
    """Get specific item."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    item = board.get_item(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item.to_dict())

@app.route("/api/<user>/items/<item_id>", methods=["PUT"])
def update_item(user, item_id):
    """Update item - AUTO-SYNCS to all calendars."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    try:
        board.update_item(item_id, **data)
        item = board.get_item(item_id)
        
        # AUTO-SYNC: Update on all calendars if due_date or status changed
        if item.due_date:
            if item.status == Status.DONE:
                # Remove from calendars when completed
                auto_sync.remove_item_from_all_calendars(item_id)
            else:
                # Update on all calendars
                auto_sync.update_item_on_all_calendars(item, user)
        
        return jsonify(item.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@app.route("/api/<user>/items/<item_id>", methods=["DELETE"])
def delete_item(user, item_id):
    """Delete item - AUTO-REMOVES from all calendars."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    board.delete_item(item_id)
    
    # AUTO-SYNC: Remove from all calendars
    auto_sync.remove_item_from_all_calendars(item_id)
    
    return jsonify({"ok": True})

@app.route("/api/<user>/items/<item_id>/move", methods=["POST"])
def move_item(user, item_id):
    """Move item to new status - AUTO-SYNCS completion."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    new_status = Status(data.get("status"))
    try:
        board.move_item(item_id, new_status)
        item = board.get_item(item_id)
        
        # AUTO-SYNC: Remove from calendars when marked done
        if new_status == Status.DONE:
            auto_sync.remove_item_from_all_calendars(item_id)
        elif item.due_date:
            # Update status on calendars
            auto_sync.update_item_on_all_calendars(item, user)
        
        return jsonify(item.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@app.route("/api/<user>/stats", methods=["GET"])
def get_stats(user):
    """Get board statistics."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "todo_count": len(board.get_items_by_status(Status.TODO)),
        "in_progress_count": len(board.get_items_by_status(Status.IN_PROGRESS)),
        "review_count": len(board.get_items_by_status(Status.REVIEW)),
        "done_count": len(board.get_items_by_status(Status.DONE)),
        "total_items": len(board.items),
        "top_priority_todo": board.get_top_priority_item(Status.TODO),
        "top_priority_in_progress": board.get_top_priority_item(Status.IN_PROGRESS),
    })

@app.route("/api/<user>/history", methods=["GET"])
def get_history(user):
    """Get completed items (TDL history)."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    tag = request.args.get("tag")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if tag:
        items = board.get_completed_items_by_tag(tag)
    elif start_date and end_date:
        items = board.get_completed_items_by_date(start_date, end_date)
    else:
        items = board.get_completed_items(limit=limit, offset=offset)

    return jsonify({
        "items": [item.to_dict() for item in items],
        "total": len(board.get_completed_items(limit=10000)),
        "stats": board.get_completion_stats(),
    })

@app.route("/api/<user>/history/stats", methods=["GET"])
def get_history_stats(user):
    """Get completion statistics."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify(board.get_completion_stats())

@app.route("/api/sync-status", methods=["GET"])
def sync_status():
    """Get auto-sync status."""
    return jsonify({
        "auto_sync_enabled": auto_sync.sync_enabled,
        "calendars_syncing_to": [
            "Outlook" if outlook_sync else None,
            "Google Calendar" if google_sync else None,
            "Apple Calendar" if apple_sync else None,
            "iCal (.ics files)" if ical_sync else None,
        ],
        "message": "All tasks automatically sync to connected calendars. No manual action needed."
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5555))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug, port=port, host="0.0.0.0")

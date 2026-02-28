#!/usr/bin/env python3
"""Scout TDL - Kanban board with multi-user support and calendar sync."""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from kanban_db import KanbanBoard, Status, Priority
from calendar_sync_teams import TeamsCalendarSync
from calendar_sync_google import GoogleCalendarSync
from calendar_sync_ical import iCalSync
import json
from pathlib import Path
import os
from datetime import datetime, timedelta
import uuid

_app_dir = Path(__file__).parent
app = Flask(__name__, template_folder=str(_app_dir / "templates"), static_folder=str(_app_dir / "static"))
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# User boards (Scout and Reid)
boards = {
    "scout": KanbanBoard("scout"),
    "reid": KanbanBoard("reid")
}

# Calendar sync instances
teams_sync = TeamsCalendarSync(
    client_id=os.environ.get("TEAMS_CLIENT_ID", ""),
    client_secret=os.environ.get("TEAMS_CLIENT_SECRET", ""),
    tenant_id=os.environ.get("TEAMS_TENANT_ID", "common")
)
google_sync = GoogleCalendarSync(
    scout_email=os.environ.get("SCOUT_EMAIL", "jeffriesr27@darden.virginia.edu"),
    scout_alt_email=os.environ.get("SCOUT_ALT_EMAIL", "dsn9zx@darden.virginia.edu")
)
ical_sync = iCalSync()

# Routes
@app.route("/")
def index():
    """Serve kanban board UI."""
    return render_template("index.html")

# Multi-user API endpoints
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
    """Create new item for user."""
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
    
    # Sync to calendars if due_date is set
    if item.due_date:
        teams_sync.add_event(item, user)
        google_sync.add_event(item, user)
        ical_sync.add_event(item, user)
    
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
    """Update item."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    try:
        board.update_item(item_id, **data)
        item = board.get_item(item_id)
        
        # Sync calendar changes
        if "due_date" in data or "status" in data:
            if item.status == Status.DONE:
                teams_sync.remove_event(item_id)
                google_sync.remove_event(item_id)
                ical_sync.remove_event(item_id)
            else:
                teams_sync.update_event(item, user)
                google_sync.update_event(item, user)
                ical_sync.update_event(item, user)
        
        return jsonify(item.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@app.route("/api/<user>/items/<item_id>", methods=["DELETE"])
def delete_item(user, item_id):
    """Delete item."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    board.delete_item(item_id)
    teams_sync.remove_event(item_id)
    google_sync.remove_event(item_id)
    ical_sync.remove_event(item_id)
    return jsonify({"ok": True})

@app.route("/api/<user>/items/<item_id>/move", methods=["POST"])
def move_item(user, item_id):
    """Move item to new status."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    new_status = Status(data.get("status"))
    try:
        board.move_item(item_id, new_status)
        item = board.get_item(item_id)
        
        # Sync completed items
        if new_status == Status.DONE:
            teams_sync.remove_event(item_id)
            google_sync.remove_event(item_id)
            ical_sync.remove_event(item_id)
        
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

# Teams OAuth routes
@app.route("/auth/teams/login")
def teams_login():
    """Initiate Teams OAuth flow."""
    auth_url, state = teams_sync.get_auth_url()
    session["oauth_state"] = state
    session["user"] = request.args.get("user", "scout")
    return redirect(auth_url)

@app.route("/auth/teams/callback")
def teams_callback():
    """Handle Teams OAuth callback."""
    user = session.get("user", "scout")
    code = request.args.get("code")
    state = request.args.get("state")
    
    if state != session.get("oauth_state"):
        return jsonify({"error": "State mismatch"}), 400
    
    try:
        teams_sync.get_token(code, user)
        return redirect("/")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/<user>/calendars/sync", methods=["POST"])
def sync_calendars(user):
    """Manually sync to all calendars."""
    board = boards.get(user)
    if not board:
        return jsonify({"error": "User not found"}), 404
    
    try:
        for item in board.items:
            if item.due_date and item.status != Status.DONE:
                teams_sync.add_event(item, user)
                google_sync.add_event(item, user)
                ical_sync.add_event(item, user)
        
        return jsonify({"ok": True, "message": "Synced to Teams, Google Calendar, and iCal"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5555))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug, port=port, host="0.0.0.0")

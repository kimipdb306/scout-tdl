#!/usr/bin/env python3
"""Kanban board Flask API."""

from flask import Flask, render_template, request, jsonify
from kanban_db import KanbanBoard, Status, Priority
from calendar_sync import sync_all
import json

app = Flask(__name__, template_folder=".", static_folder="static")
board = KanbanBoard()


@app.route("/")
def index():
    """Serve kanban board UI."""
    return render_template("index.html")


@app.route("/api/items", methods=["GET"])
def get_items():
    """Get all items grouped by status."""
    return jsonify({
        status.value: [
            item.to_dict() for item in board.get_items_by_status(status)
        ]
        for status in Status
    })


@app.route("/api/items", methods=["POST"])
def create_item():
    """Create new item."""
    data = request.json
    item = board.add_item(
        title=data.get("title"),
        priority=Priority[data.get("priority", "MEDIUM")],
        due_date=data.get("due_date"),
        description=data.get("description", "")
    )
    return jsonify(item.to_dict()), 201


@app.route("/api/items/<item_id>", methods=["GET"])
def get_item(item_id):
    """Get specific item."""
    item = board.get_item(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item.to_dict())


@app.route("/api/items/<item_id>", methods=["PUT"])
def update_item(item_id):
    """Update item."""
    data = request.json
    try:
        board.update_item(item_id, **data)
        item = board.get_item(item_id)
        return jsonify(item.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/items/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete item."""
    board.delete_item(item_id)
    return jsonify({"ok": True})


@app.route("/api/items/<item_id>/move", methods=["POST"])
def move_item(item_id):
    """Move item to new status."""
    data = request.json
    new_status = Status(data.get("status"))
    try:
        board.move_item(item_id, new_status)
        item = board.get_item(item_id)
        return jsonify(item.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/sync", methods=["POST"])
def sync_calendars():
    """Sync kanban to all calendars."""
    try:
        sync_all()
        return jsonify({"ok": True, "message": "Synced to Google Calendar, iCal, Teams"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get board statistics."""
    return jsonify({
        "todo_count": len(board.get_items_by_status(Status.TODO)),
        "in_progress_count": len(board.get_items_by_status(Status.IN_PROGRESS)),
        "review_count": len(board.get_items_by_status(Status.REVIEW)),
        "done_count": len(board.get_items_by_status(Status.DONE)),
        "total_items": len(board.items),
        "top_priority_todo": board.get_top_priority_item(Status.TODO),
        "top_priority_in_progress": board.get_top_priority_item(Status.IN_PROGRESS),
    })


@app.route("/api/history", methods=["GET"])
def get_history():
    """Get completed items (TDL history)."""
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


@app.route("/api/history/stats", methods=["GET"])
def get_history_stats():
    """Get completion statistics."""
    return jsonify(board.get_completion_stats())


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug, port=port, host="0.0.0.0")

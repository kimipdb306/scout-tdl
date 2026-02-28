#!/usr/bin/env python3
"""Kanban board data management."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

import os
_data_dir = Path(os.environ.get("DATA_DIR", str(Path(__file__).parent)))
DATA_FILE = _data_dir / "kanban_data.json"
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    TOP_PRIORITY = 4


class Status(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class KanbanItem:
    def __init__(self, id: str, title: str, status: Status = Status.TODO,
                 priority: Priority = Priority.MEDIUM, due_date: Optional[str] = None,
                 description: str = "", created_at: Optional[str] = None,
                 completed_at: Optional[str] = None, time_to_complete: Optional[int] = None,
                 tags: Optional[list] = None):
        self.id = id
        self.title = title
        self.status = status
        self.priority = priority
        self.due_date = due_date  # ISO format: YYYY-MM-DD
        self.description = description
        self.created_at = created_at or datetime.now().isoformat()
        self.completed_at = completed_at  # When marked as done
        self.time_to_complete = time_to_complete  # Seconds from created to completed
        self.tags = tags or []  # For filtering/organizing

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.name,
            "due_date": self.due_date,
            "description": self.description,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "time_to_complete": self.time_to_complete,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "KanbanItem":
        return cls(
            id=data["id"],
            title=data["title"],
            status=Status(data.get("status", "todo")),
            priority=Priority[data.get("priority", "MEDIUM")],
            due_date=data.get("due_date"),
            description=data.get("description", ""),
            created_at=data.get("created_at"),
            completed_at=data.get("completed_at"),
            time_to_complete=data.get("time_to_complete"),
            tags=data.get("tags", []),
        )


class KanbanBoard:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.items: List[KanbanItem] = []
        self.load()

    def load(self):
        """Load from disk."""
        if DATA_FILE.exists():
            data = json.loads(DATA_FILE.read_text())
            self.items = [KanbanItem.from_dict(item) for item in data]
        else:
            self.items = []

    def save(self):
        """Save to disk."""
        data = [item.to_dict() for item in self.items]
        DATA_FILE.write_text(json.dumps(data, indent=2))

    def add_item(self, title: str, priority: Priority = Priority.MEDIUM,
                 due_date: Optional[str] = None, description: str = "") -> KanbanItem:
        """Add new item."""
        item_id = f"item_{int(datetime.now().timestamp() * 1000)}"
        item = KanbanItem(item_id, title, Status.TODO, priority, due_date, description)
        self.items.append(item)
        self.save()
        return item

    def update_item(self, item_id: str, **kwargs):
        """Update item fields."""
        item = self.get_item(item_id)
        if not item:
            raise ValueError(f"Item {item_id} not found")

        for key, value in kwargs.items():
            if key == "status" and isinstance(value, str):
                item.status = Status(value)
            elif key == "priority" and isinstance(value, str):
                item.priority = Priority[value]
            else:
                setattr(item, key, value)

        # Enforce "only one top priority per column"
        if item.priority == Priority.TOP_PRIORITY:
            for other in self.items:
                if other.id != item_id and other.status == item.status and other.priority == Priority.TOP_PRIORITY:
                    other.priority = Priority.HIGH
                    print(f"Downgraded {other.id} to HIGH priority (only one TOP_PRIORITY per column)")

        self.save()

    def get_item(self, item_id: str) -> Optional[KanbanItem]:
        """Get item by ID."""
        return next((item for item in self.items if item.id == item_id), None)

    def delete_item(self, item_id: str):
        """Delete item."""
        self.items = [item for item in self.items if item.id != item_id]
        self.save()

    def get_items_by_status(self, status: Status) -> List[KanbanItem]:
        """Get all items in a status."""
        return [item for item in self.items if item.status == status]

    def get_top_priority_item(self, status: Status) -> Optional[KanbanItem]:
        """Get the top priority item in a column."""
        for item in self.get_items_by_status(status):
            if item.priority == Priority.TOP_PRIORITY:
                return item
        return None

    def get_items_by_due_date(self, start_date: str, end_date: str) -> List[KanbanItem]:
        """Get items due between dates (for calendar sync)."""
        return [item for item in self.items
                if item.due_date and start_date <= item.due_date <= end_date]

    def get_completed_items(self, limit: int = 100, offset: int = 0) -> List[KanbanItem]:
        """Get completed items (history/archive), sorted by completion date (newest first)."""
        completed = [item for item in self.items if item.status == Status.DONE and item.completed_at]
        completed.sort(key=lambda x: x.completed_at, reverse=True)
        return completed[offset:offset + limit]

    def get_completed_items_by_date(self, start_date: str, end_date: str) -> List[KanbanItem]:
        """Get completed items between dates."""
        return [item for item in self.get_completed_items(limit=10000)
                if item.completed_at and start_date <= item.completed_at[:10] <= end_date]

    def get_completed_items_by_tag(self, tag: str) -> List[KanbanItem]:
        """Get completed items with a specific tag."""
        return [item for item in self.get_completed_items(limit=10000) if tag in item.tags]

    def get_completion_stats(self) -> Dict:
        """Get stats about completed work."""
        completed = self.get_completed_items(limit=10000)
        if not completed:
            return {
                "total_completed": 0,
                "avg_time_to_complete": 0,
                "completed_this_week": 0,
                "completed_this_month": 0,
                "by_priority": {},
            }

        from datetime import timedelta
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        stats = {
            "total_completed": len(completed),
            "completed_this_week": sum(1 for item in completed if datetime.fromisoformat(item.completed_at) > week_ago),
            "completed_this_month": sum(1 for item in completed if datetime.fromisoformat(item.completed_at) > month_ago),
            "by_priority": {},
            "avg_time_to_complete": 0,
        }

        # Average time to complete
        times = [item.time_to_complete for item in completed if item.time_to_complete]
        if times:
            avg_seconds = sum(times) / len(times)
            hours = avg_seconds / 3600
            stats["avg_time_to_complete"] = f"{hours:.1f} hours"

        # By priority
        for priority in Priority:
            count = sum(1 for item in completed if item.priority == priority)
            if count > 0:
                stats["by_priority"][priority.name] = count

        return stats

    def move_item(self, item_id: str, new_status: Status):
        """Move item to new status."""
        item = self.get_item(item_id)
        if not item:
            raise ValueError(f"Item {item_id} not found")

        # If moving to same status, no need to re-check top priority
        if item.status == new_status:
            return

        # Track completion time if moving to DONE
        if new_status == Status.DONE and item.status != Status.DONE:
            item.completed_at = datetime.now().isoformat()
            # Calculate time to complete in seconds
            created = datetime.fromisoformat(item.created_at)
            completed = datetime.fromisoformat(item.completed_at)
            item.time_to_complete = int((completed - created).total_seconds())

        item.status = new_status
        self.save()

        # Re-enforce top priority rule
        if item.priority == Priority.TOP_PRIORITY:
            for other in self.items:
                if other.id != item_id and other.status == new_status and other.priority == Priority.TOP_PRIORITY:
                    other.priority = Priority.HIGH
                    self.save()

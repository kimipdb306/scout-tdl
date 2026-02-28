# Scout Kanban Board

A lightweight kanban board with calendar sync, priority management, and drag-and-drop organization.

## Features

- **4 Columns:** To Do → In Progress → Review → Done
- **4 Priority Levels:** Low, Medium, High, Top Priority (only 1 per column)
- **Due Dates:** Track deadlines with visual countdown
- **Calendar Sync:** Auto-sync to Google Calendar, iCal, Teams
- **Drag & Drop:** Move cards between columns
- **Modal Editor:** Click any card to edit or double-click to edit

## Data Storage

All data stored in `kanban_data.json` — plain JSON, version-controllable.

## Running

```bash
bash ~/.openclaw/workspace/integrations/kanban/start.sh
```

Then open: http://localhost:8000

## Calendar Integration

### Google Calendar
- Click "Sync Calendars" button in app
- All items with due dates sync to Google Calendar via `gog`
- Updates run daily via cron

### iCal
- Generated at `~/.openclaw/workspace/kanban.ics`
- Subscribe via: `webcal://localhost:8000/kanban.ics`

### Teams (Manual)
- Export kanban data, import to Teams tasks
- Teams API integration requires OAuth setup

## API Endpoints

- `GET /api/items` - Get all items by status
- `POST /api/items` - Create new item
- `GET /api/items/<id>` - Get specific item
- `PUT /api/items/<id>` - Update item
- `DELETE /api/items/<id>` - Delete item
- `POST /api/items/<id>/move` - Move to new status
- `POST /api/sync` - Sync to calendars
- `GET /api/stats` - Board statistics

## Constraints

**Top Priority Limit:**
- Only 1 item per column (To Do, In Progress, etc.) can have "Top Priority"
- Setting an item to Top Priority automatically downgrades other Top Priority items in that column to High

## Schema

```json
{
  "id": "item_1772226600000",
  "title": "Build feature X",
  "status": "in_progress",
  "priority": "TOP_PRIORITY",
  "due_date": "2026-03-15",
  "description": "Task description here",
  "created_at": "2026-02-27T23:30:00"
}
```

Status values: `todo`, `in_progress`, `review`, `done`  
Priority values: `LOW`, `MEDIUM`, `HIGH`, `TOP_PRIORITY`

## Cron Integration

Add to cron at 6:30 AM (or whenever you want):
```bash
openclaw cron add --name "kanban-sync" --cron "30 6 * * *" --tz "America/New_York" --session main --system-event 'Sync kanban to calendars: cd ~/.openclaw/workspace/integrations/kanban && python3 calendar_sync.py'
```

## Next Steps

- [ ] Teams API integration
- [ ] Recurring items (daily standup tasks)
- [ ] Time tracking (estimate vs actual)
- [ ] Notifications for due dates
- [ ] Tags/labels
- [ ] Assignees (multi-user)

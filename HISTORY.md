# TDL History (Task Archive)

The TDL (To-Do List) keeps a complete history of all completed tasks.

## Features

**View Completed Tasks**
- Click "📋 TDL History" button to see all completed items
- Sorted by completion date (newest first)
- Shows priority, completion time, due date

**Completion Statistics**
- Total tasks completed
- Tasks completed this week
- Tasks completed this month
- Average time to complete
- Breakdown by priority level

**Filter by Date Range**
- Select start and end date
- See only tasks completed in that period
- Stats update to match the filtered set

**Time Tracking**
- Every task automatically tracks how long it took to complete
- Measured from creation date to "Done" status
- Shown in hours (e.g., "2.5h")
- Used to calculate average completion time

**Search & Tags**
- Tasks can have tags for organization
- Filter by tag (coming soon)

## Data Storage

All history is stored in `kanban_data.json` with metadata:
```json
{
  "id": "item_1772226600000",
  "title": "Build feature X",
  "status": "done",
  "priority": "HIGH",
  "completed_at": "2026-02-27T18:30:00",
  "time_to_complete": 86400,  // seconds
  "tags": ["feature", "backend"],
  "created_at": "2026-02-26T18:30:00"
}
```

## Example Queries

**Find longest-running tasks**
- Sort by `time_to_complete` (descending)

**See what you completed today**
- Filter by today's date range

**Track velocity**
- Check "tasks completed this week" over time
- Use API: `GET /api/history/stats`

## API Endpoints

- `GET /api/history` -- Get completed items (paginated)
- `GET /api/history?start_date=2026-02-20&end_date=2026-02-27` -- Filter by date
- `GET /api/history?tag=work` -- Filter by tag
- `GET /api/history/stats` -- Get completion statistics only

## Integration Ideas

1. **Weekly Summary** -- Cron job emails you a summary of completed tasks
2. **Burndown Chart** -- Plot completion over time
3. **Slack Updates** -- Post completed tasks to team Slack
4. **Annual Review** -- Export full year of completed tasks for performance review

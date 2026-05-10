# local_schedule

SQLite-backed local schedule/calendar manager MCP component. Supports range-type events (with start/end times), deadline-type events, status tracking, and free-slot discovery.

## Tools

- `schedule_list_events(start_time, end_time)` — List events with optional ISO datetime range filter.
- `schedule_add_event(title, schedule_type, start_time, end_time, due_time, status, description)` — Add an event. `schedule_type=range` uses start/end times; `schedule_type=deadline` uses `due_time`.
- `schedule_update_event(event_id, title, schedule_type, start_time, end_time, due_time)` — Update event fields by ID.
- `schedule_update_status(event_id, status)` — Update event status: `未开始`, `进行中`, `已完成`.
- `schedule_delete_event(event_id)` — Delete an event by ID.
- `schedule_find_free_slots(range_start, range_end, min_minutes)` — Find gaps between busy range-type events using a merged-interval algorithm.

## Config

```toml
[local_schedule]
db_path = ""  # optional; defaults to local_schedule.sqlite3 next to component.py
```

## Dependencies

- No external Python packages (stdlib `sqlite3` only).

## Usage Notes

- All times are ISO 8601 datetime strings (e.g., `2026-05-10T14:00:00`).
- Auto-migrates schema on startup for backward compatibility.
- Cross-platform: works on Windows, Linux, and macOS.

Platforms: Windows|Linux|MacOs

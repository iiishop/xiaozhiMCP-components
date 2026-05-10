from __future__ import annotations

import pytest

from local_schedule import LocalScheduleStore


def test_add_range_event_normalizes_timezone_and_preserves_status(tmp_path):
    store = LocalScheduleStore(db_path=str(tmp_path / "schedule.sqlite3"))

    event = store.add_event(
        title="Standup",
        schedule_type="range",
        start_time="2026-05-10T09:00:00+08:00",
        end_time="2026-05-10T09:30:00+08:00",
        status="进行中",
    )

    assert event["status"] == "进行中"
    assert event["start_time"] == "2026-05-10T01:00:00"
    assert event["end_time"] == "2026-05-10T01:30:00"
    assert store.list_events()[0]["id"] == event["id"]


def test_add_deadline_event_uses_due_time_for_range_fields(tmp_path):
    store = LocalScheduleStore(db_path=str(tmp_path / "schedule.sqlite3"))

    event = store.add_event(
        title="Ship release",
        schedule_type="deadline",
        due_time="2026-05-10T12:00:00Z",
    )

    assert event["schedule_type"] == "deadline"
    assert event["due_time"] == "2026-05-10T12:00:00"
    assert event["start_time"] == "2026-05-10T12:00:00"
    assert event["end_time"] == "2026-05-10T12:00:00"


def test_update_event_status_validates_allowed_statuses(tmp_path):
    store = LocalScheduleStore(db_path=str(tmp_path / "schedule.sqlite3"))
    event = store.add_event(
        title="Focus",
        start_time="2026-05-10T09:00:00",
        end_time="2026-05-10T10:00:00",
    )

    updated = store.update_event_status(event["id"], "已完成")

    assert updated["updated"] is True
    assert updated["event"]["status"] == "已完成"
    with pytest.raises(ValueError, match="status must be one of"):
        store.update_event_status(event["id"], "blocked")


def test_list_events_filters_overlapping_time_ranges(tmp_path):
    store = LocalScheduleStore(db_path=str(tmp_path / "schedule.sqlite3"))
    store.add_event(
        title="Morning",
        start_time="2026-05-10T09:00:00",
        end_time="2026-05-10T10:00:00",
    )
    store.add_event(
        title="Afternoon",
        start_time="2026-05-10T13:00:00",
        end_time="2026-05-10T14:00:00",
    )

    events = store.list_events(start_time="2026-05-10T09:30:00", end_time="2026-05-10T12:00:00")

    assert [event["title"] for event in events] == ["Morning"]

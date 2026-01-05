# schedule_bp.py
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime, date, time, timedelta
from typing import Optional, Iterable, Tuple

from flask import Blueprint, request, jsonify, render_template, current_app

try:
    from zoneinfo import ZoneInfo
except Exception:
    from backports.zoneinfo import ZoneInfo


schedule_bp = Blueprint("schedule_bp", __name__)

# ----------------------------
# Constants (kept identical behavior)
# ----------------------------
TZ = ZoneInfo("America/Vancouver")
MIN_DATE = date(2025, 10, 1)
MAX_DATE = date(2030, 12, 31)

# SQLite DB file beside your code
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "app.db")


# ----------------------------
# DB helpers
# ----------------------------
def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, isolation_level=None)  # autocommit
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_bookings_db() -> None:
    conn = db_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          start_dt TEXT NOT NULL,          -- ISO with offset
          end_dt   TEXT NOT NULL,          -- ISO with offset
          series_id TEXT,                  -- NULL for single; =id for series
          repeat_json TEXT,                -- NULL or JSON: {"freq":"DAILY"/"WEEKLY","until":"YYYY-MM-DD"}
          exceptions_json TEXT             -- NULL or JSON array of minute_key strings
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bookings_series_id ON bookings(series_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bookings_start_dt  ON bookings(start_dt)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bookings_end_dt    ON bookings(end_dt)")
    conn.close()


def init_db(app=None) -> None:
    # app parameter kept for compatibility with app.py usage
    init_bookings_db()


def row_to_booking(row: sqlite3.Row) -> dict:
    repeat = json.loads(row["repeat_json"]) if row["repeat_json"] else None
    if repeat and "until" in repeat and isinstance(repeat["until"], str):
        repeat["until"] = date.fromisoformat(repeat["until"])

    exceptions = set(json.loads(row["exceptions_json"])) if row["exceptions_json"] else set()

    return {
        "id": row["id"],
        "title": row["title"],
        "start_dt": datetime.fromisoformat(row["start_dt"]),
        "end_dt": datetime.fromisoformat(row["end_dt"]),
        "series_id": row["series_id"],
        "repeat": repeat,
        "exceptions": exceptions,
    }


def fetch_series_rows() -> list[dict]:
    conn = db_conn()
    rows = conn.execute(
        """
        SELECT * FROM bookings
        WHERE repeat_json IS NOT NULL AND series_id = id
        """
    ).fetchall()
    conn.close()
    return [row_to_booking(r) for r in rows]


def fetch_single_overlapping(range_start: datetime, range_end: datetime) -> list[dict]:
    # singles are rows with repeat_json IS NULL (series_id can be NULL)
    conn = db_conn()
    rows = conn.execute(
        """
        SELECT * FROM bookings
        WHERE repeat_json IS NULL
          AND start_dt < ?
          AND end_dt   > ?
        """,
        (range_end.isoformat(), range_start.isoformat()),
    ).fetchall()
    conn.close()
    return [row_to_booking(r) for r in rows]


def insert_booking(rec: dict) -> None:
    conn = db_conn()
    repeat_json = json.dumps(rec["repeat"]) if rec.get("repeat") else None
    exceptions_json = (
        json.dumps(sorted(list(rec.get("exceptions", set())))) if rec.get("exceptions") else None
    )
    conn.execute(
        """
        INSERT INTO bookings (id, title, start_dt, end_dt, series_id, repeat_json, exceptions_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rec["id"],
            rec["title"],
            rec["start_dt"].isoformat(),
            rec["end_dt"].isoformat(),
            rec.get("series_id"),
            repeat_json,
            exceptions_json,
        ),
    )
    conn.close()


def delete_single_booking(booking_id: str) -> int:
    conn = db_conn()
    cur = conn.execute(
        """
        DELETE FROM bookings
        WHERE id = ?
          AND repeat_json IS NULL
        """,
        (booking_id,),
    )
    conn.close()
    return cur.rowcount


def delete_series(series_id: str) -> int:
    conn = db_conn()
    cur = conn.execute(
        """
        DELETE FROM bookings
        WHERE id = ?
          AND series_id = ?
          AND repeat_json IS NOT NULL
        """,
        (series_id, series_id),
    )
    conn.close()
    return cur.rowcount


def add_series_exception(series_id: str, occ_start_key: str) -> bool:
    conn = db_conn()
    row = conn.execute(
        """
        SELECT exceptions_json
        FROM bookings
        WHERE id = ?
          AND series_id = ?
          AND repeat_json IS NOT NULL
        """,
        (series_id, series_id),
    ).fetchone()

    if not row:
        conn.close()
        return False

    existing = set(json.loads(row["exceptions_json"])) if row["exceptions_json"] else set()
    existing.add(occ_start_key)

    conn.execute(
        "UPDATE bookings SET exceptions_json = ? WHERE id = ?",
        (json.dumps(sorted(existing)), series_id),
    )
    conn.close()
    return True


# ----------------------------
# Date/time helpers (same external behavior)
# ----------------------------
def week_start_for(d: date) -> date:
    return d - timedelta(days=d.weekday())  # Monday


def clamp_date_to_range(d: date) -> date:
    if d < MIN_DATE:
        return MIN_DATE
    if d > MAX_DATE:
        return MAX_DATE
    return d


def parse_iso_local(dt_str: str) -> datetime:
    """
    Accept 'YYYY-MM-DDTHH:MM' (naive) or full ISO with offset.
    Naive -> assume local TZ. Aware -> convert to local TZ.
    """
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def minute_key(dt: datetime) -> str:
    """Normalize to local TZ, drop seconds, keep minute precision."""
    return dt.astimezone(TZ).replace(second=0, microsecond=0).isoformat(timespec="minutes")


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def within_allowed_window(start_dt: datetime, end_dt: datetime) -> bool:
    return (MIN_DATE <= start_dt.date() <= MAX_DATE) and (MIN_DATE <= end_dt.date() <= MAX_DATE)


def is_series(rec: dict) -> bool:
    return rec.get("series_id") == rec.get("id") and rec.get("repeat") is not None


# ----------------------------
# Series expansion logic (same output contract)
# ----------------------------
def series_occurrences(series: dict, range_start: datetime, range_end: datetime):
    """Yield (occ_start, occ_end) for series within [range_start, range_end)."""
    assert is_series(series)

    freq = series["repeat"]["freq"]
    until_d: date = series["repeat"]["until"]
    exceptions = series.get("exceptions", set()) or set()

    base_start: datetime = series["start_dt"]
    base_end: datetime = series["end_dt"]
    delta = base_end - base_start

    if freq == "DAILY":
        step = timedelta(days=1)
        cur = base_start
        if base_start < range_start:
            days = int((range_start - base_start).total_seconds() // 86400)
            cur = base_start + timedelta(days=days)
            if cur < range_start:
                cur += step
    elif freq == "WEEKLY":
        step = timedelta(weeks=1)
        cur = base_start
        if base_start < range_start:
            days = int((range_start - base_start).total_seconds() // 86400)
            weeks = days // 7
            cur = base_start + timedelta(weeks=weeks)
            while cur < range_start:
                cur += step
    else:
        return

    end_limit = min(until_d, MAX_DATE)
    while cur.date() <= end_limit and cur < range_end:
        occ_start = cur
        occ_end = cur + delta
        key = minute_key(occ_start)
        if key not in exceptions:
            if overlaps(occ_start, occ_end, range_start, range_end):
                yield (occ_start, occ_end)
        cur += step


def expand_bookings(range_start: datetime, range_end: datetime):
    # Only fetch singles overlapping window + all series (series expansion decides relevance)
    singles = fetch_single_overlapping(range_start, range_end)
    series_rows = fetch_series_rows()

    items = []

    for b in series_rows:
        for occ_start, occ_end in series_occurrences(b, range_start, range_end):
            items.append(
                {
                    "id": b["id"],  # series id
                    "title": b["title"],
                    "start": occ_start.isoformat(),
                    "end": occ_end.isoformat(),
                    "series_id": b["series_id"],
                    "repeating": True,
                    "is_occurrence": True,
                }
            )

    for b in singles:
        items.append(
            {
                "id": b["id"],
                "title": b["title"],
                "start": b["start_dt"].isoformat(),
                "end": b["end_dt"].isoformat(),
                "series_id": None,
                "repeating": False,
                "is_occurrence": False,
            }
        )

    return items


# ----------------------------
# Conflict checks (same behavior)
# ----------------------------
def conflict_any(start_dt: datetime, end_dt: datetime) -> Optional[dict]:
    # 1) Singles: check via SQL quickly
    conn = db_conn()
    row = conn.execute(
        """
        SELECT id, title, start_dt, end_dt
        FROM bookings
        WHERE repeat_json IS NULL
          AND start_dt < ?
          AND end_dt   > ?
        ORDER BY start_dt ASC
        LIMIT 1
        """,
        (end_dt.isoformat(), start_dt.isoformat()),
    ).fetchone()
    conn.close()

    if row:
        return {
            "id": row["id"],
            "title": row["title"],
            "start": row["start_dt"],
            "end": row["end_dt"],
        }

    # 2) Series: expand occurrences in a limited neighborhood of candidate
    window_start = start_dt - timedelta(days=14)
    window_end = end_dt + timedelta(days=14)
    for s in fetch_series_rows():
        for occ_start, occ_end in series_occurrences(s, window_start, window_end):
            if overlaps(start_dt, end_dt, occ_start, occ_end):
                return {
                    "id": s["id"],
                    "title": s["title"],
                    "start": occ_start.isoformat(),
                    "end": occ_end.isoformat(),
                }

    return None


def conflict_series(proto_series: dict) -> Optional[dict]:
    base_start = proto_series["start_dt"]
    base_end = proto_series["end_dt"]
    until_d: date = proto_series["repeat"]["until"]
    freq: str = proto_series["repeat"]["freq"]

    step = timedelta(days=1) if freq == "DAILY" else timedelta(weeks=1)
    horizon_end = datetime.combine(min(until_d, MAX_DATE), time(23, 59), tzinfo=TZ)

    cur = base_start
    while cur <= horizon_end:
        occ_start = cur
        occ_end = cur + (base_end - base_start)
        c = conflict_any(occ_start, occ_end)
        if c:
            return c
        cur += step

    return None


# ----------------------------
# Routes (frontend remains unchanged)
# ----------------------------
@schedule_bp.get("/schedule")
def schedule_page():
    today_local = clamp_date_to_range(datetime.now(TZ).date())
    qs = request.args.get("weekStart")
    if qs:
        try:
            requested = date.fromisoformat(qs)
        except ValueError:
            requested = today_local
    else:
        requested = today_local

    ws = week_start_for(requested)
    if ws > MAX_DATE:
        ws = week_start_for(MAX_DATE)
    if (ws + timedelta(days=6)) < MIN_DATE:
        ws = week_start_for(MIN_DATE)

    return render_template(
        "schedule.html",
        week_start=ws.isoformat(),
        min_date=MIN_DATE.isoformat(),
        max_date=MAX_DATE.isoformat(),
    )


@schedule_bp.get("/api/bookings")
def api_get_bookings():
    qs = request.args.get("weekStart")
    if not qs:
        return jsonify({"error": "weekStart is required"}), 400
    try:
        ws = date.fromisoformat(qs)
    except ValueError:
        return jsonify({"error": "Invalid weekStart"}), 400

    ws = week_start_for(ws)
    start = datetime.combine(ws, time(0, 0), tzinfo=TZ)
    end = start + timedelta(days=7)

    return jsonify({"items": expand_bookings(start, end)})


@schedule_bp.post("/api/bookings")
def api_create_booking():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip() or "Booking"
    start_str = data.get("start")
    end_str = data.get("end")
    repeat = data.get("repeat")  # None or {"freq":"DAILY"/"WEEKLY","until":"YYYY-MM-DD"}

    if not start_str or not end_str:
        return jsonify({"error": "start and end are required"}), 400

    try:
        start_dt = parse_iso_local(start_str)
        end_dt = parse_iso_local(end_str)
    except Exception:
        return jsonify({"error": "Invalid datetime format"}), 400

    if end_dt <= start_dt:
        return jsonify({"error": "End must be after start"}), 400
    if not within_allowed_window(start_dt, end_dt):
        return jsonify({"error": "Booking must be within allowed window"}), 400

    # Repeating series
    if repeat:
        freq = (repeat.get("freq") or "").upper()
        if freq not in ("DAILY", "WEEKLY"):
            return jsonify({"error": "repeat.freq must be DAILY or WEEKLY"}), 400

        try:
            until_d = date.fromisoformat(repeat.get("until", ""))
        except Exception:
            return jsonify({"error": "repeat.until must be YYYY-MM-DD"}), 400

        if until_d < start_dt.date():
            return jsonify({"error": "repeat.until must be on/after start date"}), 400
        if until_d > MAX_DATE:
            until_d = MAX_DATE

        proto = {
            "id": None,
            "title": title,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "series_id": None,
            "repeat": {"freq": freq, "until": until_d},
            "exceptions": set(),
        }

        c = conflict_series(proto)
        if c:
            return jsonify({"error": "Time conflict in series", "conflicts_with": c}), 409

        series_id = str(__import__("uuid").uuid4())
        insert_booking(
            {
                "id": series_id,
                "title": title,
                "start_dt": start_dt,
                "end_dt": end_dt,
                "series_id": series_id,
                "repeat": {"freq": freq, "until": until_d.isoformat()},
                "exceptions": set(),
            }
        )
        return jsonify({"ok": True, "id": series_id, "series": True})

    # Single booking
    c = conflict_any(start_dt, end_dt)
    if c:
        return jsonify({"error": "Time conflict", "conflicts_with": c}), 409

    new_id = str(__import__("uuid").uuid4())
    insert_booking(
        {
            "id": new_id,
            "title": title,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "series_id": None,
            "repeat": None,
            "exceptions": set(),
        }
    )
    return jsonify({"ok": True, "id": new_id})


@schedule_bp.delete("/api/bookings/<booking_id>")
def api_delete_booking(booking_id: str):
    """
    Delete a single booking, a whole series, or one occurrence from a series.
      - scope=single (default)                             delete non-repeating booking by id
      - scope=series                                       delete entire series by id
      - scope=occurrence&occurrenceStart=YYYY-MM-DDTHH:MM  delete one occurrence
    """
    scope = request.args.get("scope", "single")

    if scope == "single":
        n = delete_single_booking(booking_id)
        if n == 0:
            return jsonify({"error": "Not found or not a single booking"}), 404
        return jsonify({"ok": True})

    if scope == "series":
        n = delete_series(booking_id)
        if n == 0:
            return jsonify({"error": "Series not found"}), 404
        return jsonify({"ok": True})

    if scope == "occurrence":
        occ_start_str = request.args.get("occurrenceStart")
        if not occ_start_str:
            return jsonify({"error": "occurrenceStart is required"}), 400
        try:
            occ_start = parse_iso_local(occ_start_str)
        except Exception:
            return jsonify({"error": "Invalid occurrenceStart"}), 400

        ok = add_series_exception(booking_id, minute_key(occ_start))
        if not ok:
            return jsonify({"error": "Series not found"}), 404
        return jsonify({"ok": True})

    return jsonify({"error": "Invalid scope"}), 400

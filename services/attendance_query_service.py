"""Central helpers to query attendance data consistently.

Provides:
  • get_attendance_snapshot(date, class_id, group_id) — one row per student
  • get_student_attendance_history(student_id, join_date)

Both helpers coalesce multiple logs for the same day so the UI, profile
screens, and PDF exports all share the same Present/Absent logic.
"""

from __future__ import annotations

from datetime import date as date_type, timedelta
from typing import List, Dict

from database.connection import get_session
from models.attendance import Attendance
from models.student import Student

_STATUS_PRIORITY = {
    "Present": 3,
    "Incomplete": 2,
    "Absent": 1,
}


def _priority(status: str | None) -> int:
    return _STATUS_PRIORITY.get(status or "", 0)


def _coalesce(records: List[Attendance]) -> Dict[tuple, dict]:
    """Return {(student_id, date): {entry, exit, status}}."""

    grouped: Dict[tuple, dict] = {}
    for att in records:
        key = (att.student_id, att.date)
        status = att.status or ("Present" if att.exit_time else "Incomplete")
        rec = grouped.setdefault(key, {
            "entry": att.entry_time,
            "exit": att.exit_time,
            "status": status,
        })

        if att.entry_time and (
            rec["entry"] is None or att.entry_time < rec["entry"]
        ):
            rec["entry"] = att.entry_time
        if att.exit_time and (
            rec["exit"] is None or att.exit_time > rec["exit"]
        ):
            rec["exit"] = att.exit_time
        if _priority(status) > _priority(rec["status"]):
            rec["status"] = status
    return grouped


def get_attendance_snapshot(ad_date: date_type,
                            class_id: int | None = None,
                            group_id: int | None = None) -> dict:
    """Return strict-join attendance rows plus roster metadata.

    Students without a record for `ad_date` are excluded from the `rows`
    payload.  Instead, the helper reports which students are *eligible*
    (joined on/before the requested date) and which of those should be
    labelled absent when the day qualifies as a working day (i.e. at least
    one attendance record exists anywhere in the institute).
    """

    today = date_type.today()
    result = {
        "rows": [],
        "eligible_student_ids": [],
        "absent_student_ids": [],
        "has_any_records": False,
        "is_holiday": False,
    }

    if not ad_date:
        return result

    session = get_session()
    student_q = session.query(Student)
    if class_id:
        student_q = student_q.filter(Student.class_id == class_id)
    if group_id:
        student_q = student_q.filter(Student.group_id == group_id)
    students = student_q.order_by(Student.name).all()

    eligible_students = [
        s for s in students
        if not s.join_date or ad_date >= s.join_date
    ]
    eligible_map = {s.id: s for s in eligible_students}
    eligible_ids = list(eligible_map.keys())
    result["eligible_student_ids"] = eligible_ids.copy()

    grouped: Dict[tuple, dict] = {}
    has_any_records = False
    if ad_date <= today:
        has_any_records = session.query(Attendance.id).filter(
            Attendance.date == ad_date
        ).limit(1).first() is not None

        if eligible_ids:
            records: List[Attendance] = session.query(Attendance).filter(
                Attendance.date == ad_date,
                Attendance.student_id.in_(eligible_ids)
            ).all()
            grouped = _coalesce(records)

    rows = []
    for (stu_id, _), rec in grouped.items():
        stu = eligible_map.get(stu_id)
        if not stu:
            continue
        status = rec["status"] or (
            "Present" if rec.get("exit") else "Incomplete"
        )
        rows.append({
            "student_id": stu.id,
            "user_id": stu.user_id,
            "name": stu.name,
            "class": stu.class_.name if stu.class_ else "—",
            "group": stu.group.name if stu.group else "—",
            "date": ad_date,
            "entry_time": rec.get("entry"),
            "exit_time": rec.get("exit"),
            "status": status,
        })

    rows.sort(key=lambda r: r["name"].lower())
    recorded_ids = {row["student_id"] for row in rows}

    absent_ids: List[int] = []
    if has_any_records:
        absent_ids = [
            stu.id for stu in eligible_students
            if stu.id not in recorded_ids
        ]

    result.update({
        "rows": rows,
        "absent_student_ids": absent_ids,
        "has_any_records": has_any_records,
        "is_holiday": (ad_date <= today and not has_any_records),
    })

    session.close()
    return result


def get_student_attendance_history(
    student_id: int,
    join_date: date_type | None = None,
    days: int | None = 45,
    include_absent: bool = False,
) -> list:
    """Return chronological attendance rows for a student.

    When include_absent is False, only actual attendance records are returned.
    When include_absent is True, synthetic blank rows are injected for
    missing working days up to the requested `days` window.  The optional
    `join_date` always acts as the lower bound so attendance is never shown
    prior to the official enrollment date.
    """

    session = get_session()
    query = session.query(Attendance).filter(
        Attendance.student_id == student_id
    )
    # Clamp to join date so no records appear before enrollment.
    if join_date:
        query = query.filter(Attendance.date >= join_date)
    records = query.order_by(Attendance.date.desc()).all()
    session.close()

    grouped = _coalesce(records)

    if not include_absent:
        ordered = sorted(
            grouped.items(), key=lambda item: item[0][1], reverse=True
        )
        rows = []
        for (_, day), rec in ordered:
            rows.append({
                "date": day,
                "entry_time": rec.get("entry"),
                "exit_time": rec.get("exit"),
                "status": rec["status"] or (
                    "Present" if rec.get("exit") else "Incomplete"
                ),
            })
            if days and len(rows) >= days:
                break
        return rows

    # include_absent=True path (used for analytics-style feeds)
    if records:
        latest_day = records[0].date
    else:
        latest_day = date_type.today()

    if days:
        earliest_day = latest_day - timedelta(days=max(days - 1, 0))
    else:
        earliest_day = join_date or latest_day
    if join_date and join_date > earliest_day:
        earliest_day = join_date

    working_days = set()
    if earliest_day and latest_day and earliest_day <= latest_day:
        work_session = get_session()
        working_rows = work_session.query(Attendance.date).filter(
            Attendance.date >= earliest_day,
            Attendance.date <= latest_day,
        ).distinct().all()
        work_session.close()
        working_days = {row[0] for row in working_rows}

    rows = []
    day = latest_day
    limit = days if days is not None else 365
    while day >= earliest_day:
        rec = grouped.get((student_id, day))
        if rec:
            status = rec["status"] or (
                "Present" if rec.get("exit") else "Incomplete"
            )
            entry = rec.get("entry")
            exit_ = rec.get("exit")
        else:
            entry = None
            exit_ = None
            if day in working_days:
                status = "Absent"
            else:
                status = "Holiday"
        rows.append({
            "date": day,
            "entry_time": entry,
            "exit_time": exit_,
            "status": status,
        })
        if limit and len(rows) >= limit:
            break
        day -= timedelta(days=1)

    return rows

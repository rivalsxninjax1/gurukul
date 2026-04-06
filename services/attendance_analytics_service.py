"""
Monthly attendance analytics.
Holiday logic: a day with NO student attendance records at all = Holiday.
Working day  : any day that has at least one student attendance record.
Present      : student has an attendance record with status 'Present'.
Absent       : student has no record on a working day.
Incomplete   : student has a record with status 'Incomplete'.
"""
from datetime import date, timedelta
from calendar import monthrange
from database.connection import get_session
from models.attendance import Attendance
from models.student import Student
import logging

logger = logging.getLogger(__name__)


def _get_all_days_in_month(year: int, month: int) -> list:
    _, last_day = monthrange(year, month)
    return [date(year, month, d) for d in range(1, last_day + 1)]


def _get_working_days(year: int, month: int) -> set:
    """Days where at least ONE student has an attendance record."""
    session = get_session()
    days_all = _get_all_days_in_month(year, month)
    working  = set()
    for d in days_all:
        count = session.query(Attendance).filter_by(date=d).count()
        if count > 0:
            working.add(d)
    session.close()
    return working


def get_monthly_analytics(student_id: int,
                           year: int, month: int) -> dict:
    """
    Returns:
        working_days   : total working days (non-holiday)
        present        : days student was present
        incomplete     : days student was incomplete
        absent         : working days - present - incomplete
        holiday        : calendar days - working days
    """
    working_days = _get_working_days(year, month)

    session = get_session()
    records = session.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.date >= date(year, month, 1),
        Attendance.date <= date(year, month,
                                monthrange(year, month)[1])
    ).all()
    session.close()

    student_days = {r.date: r.status for r in records}

    present    = 0
    incomplete = 0
    absent     = 0

    for d in working_days:
        status = student_days.get(d)
        if status == "Present":
            present += 1
        elif status == "Incomplete":
            incomplete += 1
        else:
            absent += 1

    _, last = monthrange(year, month)
    total_calendar = last
    holiday = total_calendar - len(working_days)

    return {
        "year":         year,
        "month":        month,
        "working_days": len(working_days),
        "present":      present,
        "incomplete":   incomplete,
        "absent":       absent,
        "holiday":      holiday,
        "total_calendar": total_calendar,
    }


def get_two_month_analytics(student_id: int) -> dict:
    """Returns analytics for current month and previous month."""
    today   = date.today()
    cur_y, cur_m = today.year, today.month

    if cur_m == 1:
        prev_y, prev_m = cur_y - 1, 12
    else:
        prev_y, prev_m = cur_y, cur_m - 1

    current  = get_monthly_analytics(student_id, cur_y,  cur_m)
    previous = get_monthly_analytics(student_id, prev_y, prev_m)
    return {"current": current, "previous": previous}
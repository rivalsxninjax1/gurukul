"""
Monthly attendance analytics using BS (Bikram Sambat) months.

Holiday logic:
  A day with NO attendance records for ANY student = Holiday.
  Working day = at least one student has an attendance record.

Present    : student record with status 'Present'
Incomplete : student record with status 'Incomplete'
Absent     : no record on a working day (after join date)
Holiday    : no records at all for any student that day
"""
from datetime import date
from database.connection import get_session
from models.attendance import Attendance, TeacherAttendance
from utils.bs_converter import (
    bs_month_ad_range, today_bs_tuple, prev_bs_month, ad_to_bs
)
import logging

logger = logging.getLogger(__name__)


def _get_working_days_in_ad_range(ad_start: date, ad_end: date) -> set:
    """
    Return set of AD dates in [ad_start, ad_end] where at least one
    student attendance record exists.
    """
    if not ad_start or not ad_end:
        return set()
    session = get_session()
    records = session.query(Attendance.date).filter(
        Attendance.date >= ad_start,
        Attendance.date <= ad_end,
    ).distinct().all()
    session.close()
    return {r[0] for r in records}


def get_monthly_analytics(student_id: int,
                           bs_year: int, bs_month: int,
                           join_date: date = None) -> dict:
    """
    Returns attendance analytics for a student in a given BS month.
    Only counts days on or after join_date.
    """
    ad_start, ad_end = bs_month_ad_range(bs_year, bs_month)
    if not ad_start or not ad_end:
        return _empty(bs_year, bs_month)

    # Clamp to join date
    if join_date and ad_start < join_date:
        ad_start = join_date
    if ad_start > ad_end:
        return _empty(bs_year, bs_month)

    working_days = _get_working_days_in_ad_range(ad_start, ad_end)

    # Filter to days >= join_date
    if join_date:
        working_days = {d for d in working_days if d >= join_date}

    session = get_session()
    records = session.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.date >= ad_start,
        Attendance.date <= ad_end,
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

    # Total calendar days in this BS month from join date
    from calendar import monthrange as _mr
    import datetime
    total_cal = (ad_end - ad_start).days + 1
    holiday   = total_cal - len(working_days)

    return {
        "bs_year":      bs_year,
        "bs_month":     bs_month,
        "working_days": len(working_days),
        "present":      present,
        "incomplete":   incomplete,
        "absent":       absent,
        "holiday":      max(0, holiday),
        "total_calendar": total_cal,
    }


def _empty(bs_year, bs_month):
    return {
        "bs_year": bs_year, "bs_month": bs_month,
        "working_days": 0, "present": 0,
        "incomplete": 0, "absent": 0,
        "holiday": 0, "total_calendar": 0,
    }


def get_two_month_analytics(student_id: int,
                              join_date: date = None) -> dict:
    """Returns analytics for current and previous BS month."""
    by, bm, _ = today_bs_tuple()
    py, pm    = prev_bs_month(by, bm)

    current  = get_monthly_analytics(student_id, by,  bm,  join_date)
    previous = get_monthly_analytics(student_id, py, pm,  join_date)
    return {"current": current, "previous": previous}


def get_teacher_monthly_analytics(teacher_id: int,
                                  bs_year: int, bs_month: int,
                                  join_date: date | None = None) -> dict:
    """
    Teacher analytics: any day with student or teacher attendance counts
    as a working day. Absent = working day without this teacher's record.
    """
    ad_start, ad_end = bs_month_ad_range(bs_year, bs_month)
    if not ad_start or not ad_end:
        return _empty(bs_year, bs_month)

    if join_date and ad_end < join_date:
        return _empty(bs_year, bs_month)
    if join_date and ad_start < join_date:
        ad_start = join_date
    if ad_start > ad_end:
        return _empty(bs_year, bs_month)

    session = get_session()
    student_days = set(
        r[0] for r in session.query(Attendance.date).filter(
            Attendance.date >= ad_start,
            Attendance.date <= ad_end,
        ).distinct().all()
    )
    teacher_days_all = set(
        r[0] for r in session.query(TeacherAttendance.date).filter(
            TeacherAttendance.date >= ad_start,
            TeacherAttendance.date <= ad_end,
        ).distinct().all()
    )
    working_days = student_days | teacher_days_all

    teacher_records = session.query(TeacherAttendance).filter(
        TeacherAttendance.teacher_id == teacher_id,
        TeacherAttendance.date >= ad_start,
        TeacherAttendance.date <= ad_end,
    ).all()
    session.close()

    teacher_day_map = {r.date: r.status for r in teacher_records}

    present    = 0
    incomplete = 0
    absent     = 0

    for d in working_days:
        status = teacher_day_map.get(d)
        if status == "Present":
            present += 1
        elif status == "Incomplete":
            incomplete += 1
        else:
            absent += 1

    total_cal = (ad_end - ad_start).days + 1
    holiday   = total_cal - len(working_days)

    return {
        "bs_year":        bs_year,
        "bs_month":       bs_month,
        "working_days":   len(working_days),
        "present":        present,
        "incomplete":     incomplete,
        "absent":         absent,
        "holiday":        max(0, holiday),
        "total_calendar": total_cal,
    }


def get_teacher_two_month_analytics(teacher_id: int,
                                    join_date: date | None = None) -> dict:
    by, bm, _ = today_bs_tuple()
    py, pm    = prev_bs_month(by, bm)
    current  = get_teacher_monthly_analytics(teacher_id, by, bm, join_date)
    previous = get_teacher_monthly_analytics(teacher_id, py, pm, join_date)
    return {"current": current, "previous": previous}


# BS month names (Nepali months in English)
BS_MONTH_NAMES = [
    "Baisakh", "Jestha", "Ashadh", "Shrawan",
    "Bhadra",  "Ashwin", "Kartik", "Mangsir",
    "Poush",   "Magh",   "Falgun", "Chaitra",
]

def bs_month_name(month: int) -> str:
    if 1 <= month <= 12:
        return BS_MONTH_NAMES[month - 1]
    return str(month)

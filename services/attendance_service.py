import pandas as pd
from database.connection import get_session
from models.attendance import Attendance, AttendanceLog, TeacherAttendance
from models.attendance_raw import AttendanceRawLog, UnmatchedAttendanceLog
from models.student import Student
from models.teacher import Teacher
import logging
import os

logger = logging.getLogger(__name__)


def import_attendance_excel(filepath: str, col_map: dict) -> dict:
    """
    col_map keys:
      user_id   → column for user id
      timestamp → combined datetime  (Format 1)
      date      → date column        (Format 2)
      time      → time column        (Format 2)

    Routing:
      IDs starting with 'T' → Teacher (stores entry + exit)
      All others            → Student (stores entry + exit)
    """
    session  = get_session()
    results  = {"success": 0, "errors": [], "unknown_ids": []}
    src_file = os.path.basename(filepath)

    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        session.close()
        return {"success": 0,
                "errors": [f"Cannot read file: {e}"],
                "unknown_ids": []}

    # ── Normalise user_id ─────────────────────────────────────────────────────
    uid_col = col_map.get("user_id", "user_id")
    if uid_col not in df.columns:
        session.close()
        return {"success": 0,
                "errors": [f"Column '{uid_col}' not found."],
                "unknown_ids": []}

    df = df.rename(columns={uid_col: "user_id"})
    df = df.dropna(subset=["user_id"])
    df["user_id"] = df["user_id"].astype(str).str.strip()

    # ── Normalise timestamp ───────────────────────────────────────────────────
    if "timestamp" in col_map and col_map["timestamp"] in df.columns:
        df = df.rename(columns={col_map["timestamp"]: "ts_raw"})
    elif "date" in col_map and "time" in col_map:
        dc, tc = col_map["date"], col_map["time"]
        if dc not in df.columns or tc not in df.columns:
            session.close()
            return {"success": 0,
                    "errors": ["Date or Time column not found."],
                    "unknown_ids": []}
        df["ts_raw"] = df[dc].astype(str) + " " + df[tc].astype(str)
    else:
        session.close()
        return {"success": 0,
                "errors": ["Cannot determine timestamp columns."],
                "unknown_ids": []}

    # ── Store raw logs ────────────────────────────────────────────────────────
    for _, row in df.iterrows():
        try:
            session.add(AttendanceRawLog(
                user_id     = str(row["user_id"]),
                timestamp   = str(row["ts_raw"]),
                source_file = src_file,
            ))
            session.flush()
        except Exception:
            session.rollback()

    # ── Parse timestamps ──────────────────────────────────────────────────────
    df["timestamp"] = pd.to_datetime(df["ts_raw"], errors="coerce")
    for _, row in df[df["timestamp"].isna()].iterrows():
        results["errors"].append(
            f"Invalid datetime for {row['user_id']}: '{row['ts_raw']}'"
        )
    df = df.dropna(subset=["timestamp"])
    df["date"] = df["timestamp"].dt.date

    # ── Pre-load lookup dicts ─────────────────────────────────────────────────
    all_students = {s.user_id: s.id for s in session.query(Student).all()}
    all_teachers = {t.user_id: t.id for t in session.query(Teacher).all()}

    # ── Process groups ────────────────────────────────────────────────────────
    seen_unknown = set()
    for (uid, date_val), group in df.groupby(["user_id", "date"]):
        group      = group.sort_values("timestamp")
        entry_time = group["timestamp"].iloc[0].time()
        exit_time  = (group["timestamp"].iloc[-1].time()
                      if len(group) > 1 else None)

        uid_str       = str(uid)
        is_teacher_id = uid_str.upper().startswith("T")

        student_id = all_students.get(uid_str)
        teacher_id = all_teachers.get(uid_str)
        matched    = False

        if teacher_id and is_teacher_id:
            # Teachers: store entry AND exit
            status_t = "Present" if exit_time else "Incomplete"
            exists = session.query(TeacherAttendance).filter_by(
                teacher_id=teacher_id, date=date_val
            ).first()
            if not exists:
                session.add(TeacherAttendance(
                    teacher_id  = teacher_id,
                    date        = date_val,
                    entry_time  = entry_time,
                    exit_time   = exit_time,
                    status      = status_t,
                    source_file = src_file,
                ))
                results["success"] += 1
            matched = True

        elif student_id and not is_teacher_id:
            status_s = "Present" if exit_time else "Incomplete"
            exists = session.query(Attendance).filter_by(
                student_id=student_id, date=date_val
            ).first()
            if not exists:
                session.add(Attendance(
                    student_id = student_id,
                    date       = date_val,
                    entry_time = entry_time,
                    exit_time  = exit_time,
                    status     = status_s,
                ))
                results["success"] += 1
            matched = True

        # Fallback — try either
        if not matched:
            if student_id:
                status_s = "Present" if exit_time else "Incomplete"
                exists = session.query(Attendance).filter_by(
                    student_id=student_id, date=date_val
                ).first()
                if not exists:
                    session.add(Attendance(
                        student_id = student_id,
                        date       = date_val,
                        entry_time = entry_time,
                        exit_time  = exit_time,
                        status     = status_s,
                    ))
                    results["success"] += 1
                matched = True
            elif teacher_id:
                status_t = "Present" if exit_time else "Incomplete"
                exists = session.query(TeacherAttendance).filter_by(
                    teacher_id=teacher_id, date=date_val
                ).first()
                if not exists:
                    session.add(TeacherAttendance(
                        teacher_id  = teacher_id,
                        date        = date_val,
                        entry_time  = entry_time,
                        exit_time   = exit_time,
                        status      = status_t,
                        source_file = src_file,
                    ))
                    results["success"] += 1
                matched = True

        if not matched and uid_str not in seen_unknown:
            seen_unknown.add(uid_str)
            results["unknown_ids"].append(uid_str)
            session.add(UnmatchedAttendanceLog(
                user_id   = uid_str,
                timestamp = str(group["timestamp"].iloc[0]),
                reason    = "No matching student or teacher",
            ))

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        results["errors"].append(f"Database error: {e}")
    finally:
        session.close()

    return results
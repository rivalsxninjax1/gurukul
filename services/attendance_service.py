"""
Attendance Excel import service.

CRITICAL FIX: Each row is processed independently.
  - Timestamp parsed per-row using explicit format detection
  - AD date extracted per-row via ts.date()
  - NO column-level date conversion
  - NO groupby (replaced with dict-based per-student-per-day deduplication)
  - Debug logging prints AD → BS per row for validation

Expected output (sample):
  uid=1001 AD=2026-04-01 BS=2082-12-19 entry=08:00:00 exit=16:00:00
  uid=1001 AD=2026-04-02 BS=2082-12-20 entry=08:05:00 exit=15:58:00
  uid=T101 AD=2026-04-01 BS=2082-12-19 entry=07:50:00 exit=17:00:00
"""

import pandas as pd
from database.connection import get_session
from models.attendance import Attendance, TeacherAttendance
from models.attendance_raw import AttendanceRawLog, UnmatchedAttendanceLog
from models.student import Student
from models.teacher import Teacher
from utils.bs_converter import bs_str
import logging
import os
import math
import re
from datetime import datetime as dt_type, date as date_type, time as time_type

logger = logging.getLogger(__name__)

# Explicit timestamp formats — tried in priority order, no auto-inference
_TS_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%d %H:%M%z",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %H:%M:%S%z",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S%z",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M%z",
]


_DUP_DATE_RE = re.compile(r"^([0-9]{4}[-/][0-9]{2}[-/][0-9]{2}) +\1\b(.*)$")


def _normalize_ts_string(value) -> str:
    """Trim, collapse whitespace, drop duplicated date fragments."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in ("nan", "nat", "none"):
        return ""
    text = text.replace("\u00a0", " ")
    text = " ".join(text.split())
    match = _DUP_DATE_RE.match(text)
    if match:
        suffix = match.group(2).strip()
        text = f"{match.group(1)} {suffix}" if suffix else match.group(1)
    return text


def _strip_timezone(ts):
    """Drop timezone info without shifting the clock time."""
    if ts is None:
        return None
    if getattr(ts, "tzinfo", None):
        try:
            return ts.tz_localize(None)
        except Exception:
            try:
                return ts.replace(tzinfo=None)
            except Exception:
                pass
    return ts


def _clean_date_value(val) -> str:
    if val is None:
        return ""
    if isinstance(val, dt_type):
        return val.date().isoformat()
    if isinstance(val, date_type):
        return val.isoformat()
    if isinstance(val, (int, float)):
        try:
            if math.isnan(val):
                return ""
        except TypeError:
            pass
        converted = pd.to_datetime(
            val, unit="D", origin="1899-12-30", errors="coerce"
        )
        if not pd.isna(converted):
            return converted.date().isoformat()
    text = str(val).strip()
    if text in ("", "nan", "NaT", "None"):
        return ""
    parsed = pd.to_datetime(text, errors="coerce")
    if not pd.isna(parsed):
        return parsed.date().isoformat()
    for sep in ("T", " "):
        if sep in text:
            return text.split(sep)[0]
    return text


def _clean_time_value(val) -> str:
    if val is None:
        return ""
    if isinstance(val, time_type):
        return val.strftime("%H:%M:%S")
    if isinstance(val, dt_type):
        return val.time().strftime("%H:%M:%S")
    if isinstance(val, (int, float)):
        try:
            if math.isnan(val):
                return ""
        except TypeError:
            pass
        converted = pd.to_datetime(
            val, unit="D", origin="1899-12-30", errors="coerce"
        )
        if not pd.isna(converted):
            return converted.time().strftime("%H:%M:%S")
    text = str(val).strip()
    if text in ("", "nan", "NaT", "None"):
        return ""
    parsed = pd.to_datetime(text, errors="coerce")
    if not pd.isna(parsed):
        return parsed.time().strftime("%H:%M:%S")
    for sep in ("T", " "):
        if sep in text:
            text = text.split(sep)[-1]
            break
    if text.count(":") == 1:
        text = f"{text}:00"
    return text


def _detect_format(sample_values: list) -> str | None:
    """
    Detect the dominant timestamp format from a list of string samples.
    Returns format string if >= 75% parse successfully, else None.
    """
    clean = [str(v).strip() for v in sample_values
             if v and str(v).strip() not in ("nan", "None", "NaT", "")]
    if not clean:
        return None

    for fmt in _TS_FORMATS:
        success = 0
        for val in clean:
            try:
                pd.to_datetime(val, format=fmt)
                success += 1
            except Exception:
                pass
        if success / len(clean) >= 0.75:
            logger.info(f"Detected timestamp format: {fmt}")
            return fmt

    logger.warning("No dominant format detected — will try all per row")
    return None


def _parse_timestamp_str(ts_str: str, fmt: str | None):
    """
    STRICT parsing — NO fallback guessing.
    Returns valid pd.Timestamp OR None.
    """

    ts_str = str(ts_str).strip()

    if ts_str in ("", "nan", "None", "NaT"):
        return None

    # 1. Try detected format ONLY
    if fmt:
        try:
            return pd.to_datetime(ts_str, format=fmt, errors="raise")
        except Exception:
            return None

    # 2. Try known formats STRICTLY
    for f in _TS_FORMATS:
        try:
            return pd.to_datetime(ts_str, format=f, errors="raise")
        except Exception:
            continue

    # ❌ NO mixed parsing
    return None


def import_attendance_excel(filepath: str, col_map: dict) -> dict:
    """
    Import attendance from Excel. Processes EACH ROW independently.

    col_map keys:
      user_id    → column name for user ID
      timestamp  → combined datetime column      (Format 1)
      date       → date column                   (Format 2 & 3)
      time       → time column                   (Format 2)
      entry_time → entry/punch-in time column    (Format 3)
      exit_time  → exit/punch-out time column    (Format 3, optional)

    ID routing:
      Starts with 'T' → TeacherAttendance
      Otherwise       → Student Attendance

    Per-student-per-day deduplication:
      First entry = entry_time
      Last entry  = exit_time (if > 1 record that day)
    """
    session  = get_session()
    results  = {"success": 0, "errors": [], "unknown_ids": []}
    src_file = os.path.basename(filepath)

    # ── Read Excel ────────────────────────────────────────────────────────────
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        session.close()
        return {"success": 0,
                "errors": [f"Cannot read file: {e}"],
                "unknown_ids": []}

    # ── Normalise user_id column ──────────────────────────────────────────────
    uid_col = col_map.get("user_id", "user_id")
    if uid_col not in df.columns:
        session.close()
        return {"success": 0,
                "errors": [f"Column '{uid_col}' not found in Excel."],
                "unknown_ids": []}
    df = df.rename(columns={uid_col: "_uid_"})
    df = df.dropna(subset=["_uid_"])
    df["_uid_"] = df["_uid_"].astype(str).str.strip()

    def _append_record(uid: str, raw_val, src_row):
        norm = _normalize_ts_string(raw_val)
        if not norm:
            return
        records.append({
            "_uid_": uid,
            "_ts_raw_": norm,
            "_raw_value": str(raw_val).strip(),
            "_src_row": src_row,
        })

    records = []

    if "timestamp" in col_map:
        ts_col = col_map["timestamp"]
        if ts_col not in df.columns:
            session.close()
            return {
                "success": 0,
                "errors": [f"Timestamp column '{ts_col}' not found."],
                "unknown_ids": []
            }
        for idx, row in df.iterrows():
            uid = str(row["_uid_"]).strip()
            _append_record(uid, row[ts_col], idx)

    elif "date" in col_map and "time" in col_map:
        dc = col_map["date"]
        tc = col_map["time"]
        if dc not in df.columns or tc not in df.columns:
            session.close()
            return {
                "success": 0,
                "errors": ["Date or Time column not found."],
                "unknown_ids": []
            }
        for idx, row in df.iterrows():
            uid = str(row["_uid_"]).strip()
            d = _clean_date_value(row[dc])
            t = _clean_time_value(row[tc])
            if not d:
                continue
            if not t:
                t = "00:00:00"
            _append_record(uid, f"{d} {t}", idx)

    elif "date" in col_map and "entry_time" in col_map:
        dc = col_map["date"]
        entry_col = col_map["entry_time"]
        exit_col = col_map.get("exit_time")
        missing = [
            name for name in [dc, entry_col, exit_col]
            if name and name not in df.columns
        ]
        if missing:
            session.close()
            return {
                "success": 0,
                "errors": [f"Column(s) not found: {', '.join(missing)}"],
                "unknown_ids": []
            }
        for idx, row in df.iterrows():
            uid = str(row["_uid_"]).strip()
            d = _clean_date_value(row[dc])
            if not d:
                continue
            times = []
            entry_val = _clean_time_value(row[entry_col])
            if entry_val:
                times.append(entry_val)
            if exit_col:
                exit_val = _clean_time_value(row[exit_col])
                if exit_val:
                    times.append(exit_val)
            if not times:
                continue
            for t in times:
                _append_record(uid, f"{d} {t}", idx)

    else:
        session.close()
        return {"success": 0,
                "errors": ["Cannot determine timestamp columns."],
                "unknown_ids": []}

    if not records:
        session.close()
        return {
            "success": 0,
            "errors": ["No usable timestamp rows found in the Excel file."],
            "unknown_ids": []
        }

    df = pd.DataFrame(records)

    # ── Detect dominant format from a sample ─────────────────────────────────
    sample = df["_ts_raw_"].dropna().head(100).tolist()
    detected_fmt = _detect_format(sample)

    # ── Pre-load all student/teacher ID maps ──────────────────────────────────
    all_students = {s.user_id: s.id for s in session.query(Student).all()}
    all_teachers = {t.user_id: t.id for t in session.query(Teacher).all()}

    # ── Per-row processing ────────────────────────────────────────────────────
    # Structure: {(uid_str, date_val): [timestamps...]}
    # We collect all timestamps per (uid, date) first, then deduplicate.
    daily_records: dict[tuple, list] = {}
    parse_errors = []

    for row_idx, row in df.iterrows():
        uid_str = str(row["_uid_"]).strip()
        ts_raw = row["_ts_raw_"]
        src_row = row.get("_src_row", row_idx)
        raw_display = row.get("_raw_value", ts_raw)

        if ts_raw is None or str(ts_raw).strip() in ("", "nan"):
            logger.error(f"[EMPTY DATETIME] Row {src_row}")
            continue

        ts_raw = str(ts_raw).strip()

        # ── STEP 1: Parse this row's timestamp individually ───────────────────
        ts = _parse_timestamp_str(ts_raw, detected_fmt)

        if ts is None:
            logger.error(f"[PARSE FAIL] Row {src_row} → {raw_display}")
            parse_errors.append(
                f"Row {src_row}: Invalid timestamp for {uid_str}: '{raw_display}'"
            )
            continue

        ts = _strip_timezone(ts)

       # 🔥 CRITICAL DEBUG
        logger.info(f"[ROW CHECK] uid={uid_str} raw={ts_raw} parsed={ts}")

        # ── STEP 2: Extract this row's date individually ──────────────────────
        date_val = ts.date()
        logger.info(f"[DATE CHECK] AD={date_val}")


        # ── STEP 3: Debug log — AD → BS per row ──────────────────────────────
        bs_date_str = bs_str(date_val)
        logger.info(f"[BS CHECK] AD={date_val} → BS={bs_date_str}")

        logger.debug(
            f"  uid={uid_str} AD={date_val} BS={bs_date_str} "
            f"time={ts.time()}"
        )

        # ── STEP 4: Store raw log ─────────────────────────────────────────────
        try:
            session.add(AttendanceRawLog(
                user_id     = uid_str,
                timestamp   = str(raw_display),
                source_file = src_file,
            ))
            session.flush()
        except Exception:
            session.rollback()

        # ── STEP 5: Accumulate into daily_records for dedup ──────────────────
        key = (uid_str, date_val)
        if key not in daily_records:
            daily_records[key] = []
        daily_records[key].append(ts)

    results["errors"].extend(parse_errors)

    # ── STEP 6: Process each (uid, date) group ────────────────────────────────
    seen_unknown = set()

    for (uid_str, date_val), timestamps in daily_records.items():
        timestamps.sort()
        entry_time = timestamps[0].time()
        exit_time  = timestamps[-1].time() if len(timestamps) > 1 else None

        is_teacher_id = uid_str.upper().startswith("T")
        student_id    = all_students.get(uid_str)
        teacher_id    = all_teachers.get(uid_str)
        matched       = False

        # Teacher route
        if teacher_id and is_teacher_id:
            status = "Present" if exit_time else "Incomplete"
            exists = session.query(TeacherAttendance).filter_by(
                teacher_id=teacher_id, date=date_val
            ).first()
            if not exists:
                session.add(TeacherAttendance(
                    teacher_id  = teacher_id,
                    date        = date_val,
                    entry_time  = entry_time,
                    exit_time   = exit_time,
                    status      = status,
                    source_file = src_file,
                ))
                results["success"] += 1
            matched = True

        # Student route
        elif student_id and not is_teacher_id:
            status = "Present" if exit_time else "Incomplete"
            exists = session.query(Attendance).filter_by(
                student_id=student_id, date=date_val
            ).first()
            if not exists:
                session.add(Attendance(
                    student_id = student_id,
                    date       = date_val,
                    entry_time = entry_time,
                    exit_time  = exit_time,
                    status     = status,
                ))
                results["success"] += 1
            matched = True

        # Fallback — try either direction
        if not matched:
            if student_id:
                status = "Present" if exit_time else "Incomplete"
                exists = session.query(Attendance).filter_by(
                    student_id=student_id, date=date_val
                ).first()
                if not exists:
                    session.add(Attendance(
                        student_id = student_id,
                        date       = date_val,
                        entry_time = entry_time,
                        exit_time  = exit_time,
                        status     = status,
                    ))
                    results["success"] += 1
                matched = True
            elif teacher_id:
                status = "Present" if exit_time else "Incomplete"
                exists = session.query(TeacherAttendance).filter_by(
                    teacher_id=teacher_id, date=date_val
                ).first()
                if not exists:
                    session.add(TeacherAttendance(
                        teacher_id  = teacher_id,
                        date        = date_val,
                        entry_time  = entry_time,
                        exit_time   = exit_time,
                        status      = status,
                        source_file = src_file,
                    ))
                    results["success"] += 1
                matched = True

        if not matched and uid_str not in seen_unknown:
            seen_unknown.add(uid_str)
            results["unknown_ids"].append(uid_str)
            session.add(UnmatchedAttendanceLog(
                user_id   = uid_str,
                timestamp = str(timestamps[0]),
                reason    = "No matching student or teacher ID",
            ))

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        results["errors"].append(f"Database commit error: {e}")
    finally:
        session.close()

    return results

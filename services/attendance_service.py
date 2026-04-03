import pandas as pd
from datetime import datetime
from database.connection import get_session
from models.attendance import Attendance, AttendanceLog
from models.student import Student
import logging

logger = logging.getLogger(__name__)

def import_attendance_excel(filepath: str, col_map: dict) -> dict:
    """
    col_map example: {"user_id": "UserID", "timestamp": "DateTime"}
    Returns: {"success": int, "errors": list, "unknown_ids": list}
    """
    session = get_session()
    results = {"success": 0, "errors": [], "unknown_ids": []}
    batch_name = filepath.split("\\")[-1]

    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        return {"success": 0, "errors": [f"Cannot read file: {e}"], "unknown_ids": []}

    # Rename columns using mapping
    try:
        df = df.rename(columns={
            col_map["timestamp"]: "timestamp",
            col_map["user_id"]:   "user_id"
        })
    except KeyError as e:
        return {"success": 0, "errors": [f"Column not found: {e}"], "unknown_ids": []}

    if "user_id" not in df.columns or "timestamp" not in df.columns:
        return {"success": 0, "errors": ["Required columns missing after mapping."], "unknown_ids": []}

    # Log every raw row
    for _, row in df.iterrows():
        log = AttendanceLog(
            raw_user_id  = str(row.get("user_id", "")),
            timestamp    = str(row.get("timestamp", "")),
            import_batch = batch_name
        )
        session.add(log)

    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    invalid_rows = df[df["timestamp"].isna()]
    for _, row in invalid_rows.iterrows():
        results["errors"].append(f"Invalid timestamp for user_id: {row['user_id']}")

    df = df.dropna(subset=["timestamp"])
    df["date"] = df["timestamp"].dt.date

    # Group by user_id + date
    grouped = df.groupby(["user_id", "date"])

    for (uid, date), group in grouped:
        group = group.sort_values("timestamp")
        entry_time = group["timestamp"].iloc[0].time()
        exit_time  = group["timestamp"].iloc[-1].time() if len(group) > 1 else None
        status = "Present" if exit_time else "Incomplete"

        # Find student
        student = session.query(Student).filter_by(user_id=str(uid)).first()
        if not student:
            results["unknown_ids"].append(str(uid))
            # Update log with error note
            session.query(AttendanceLog).filter_by(
                raw_user_id=str(uid), import_batch=batch_name
            ).update({"error_note": "Unknown user_id"})
            continue

        # Check for duplicate
        existing = session.query(Attendance).filter_by(
            student_id=student.id, date=date
        ).first()
        if existing:
            continue  # Skip duplicate

        att = Attendance(
            student_id = student.id,
            date       = date,
            entry_time = entry_time,
            exit_time  = exit_time,
            status     = status
        )
        session.add(att)
        results["success"] += 1

    session.commit()
    session.close()
    return results
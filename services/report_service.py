import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from database.connection import get_session
from models.attendance import Attendance
from models.student import Student
from models.subscription import StudentSubscription, SubscriptionPayment
from datetime import date as date_type
import logging

logger = logging.getLogger(__name__)


# ── Attendance report ─────────────────────────────────────────────────────────

def get_attendance_report(start_date: date_type, end_date: date_type,
                          class_id=None) -> list:
    session = get_session()
    rows    = session.query(Attendance).filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()
    result = []
    for att in rows:
        s = att.student
        if class_id and s and s.class_id != class_id:
            continue
        result.append({
            "user_id": s.user_id if s else "?",
            "name":    s.name    if s else "Unknown",
            "class":   s.class_.name if s and s.class_ else "—",
            "group":   s.group.name  if s and s.group  else "—",
            "date":    str(att.date),
            "entry":   str(att.entry_time) if att.entry_time else "—",
            "exit":    str(att.exit_time)  if att.exit_time  else "—",
            "status":  att.status,
        })
    session.close()
    return result


def export_attendance_excel(rows: list, filepath: str):
    pd.DataFrame(rows).to_excel(filepath, index=False)
    logger.info(f"Attendance Excel: {filepath}")


def export_attendance_pdf(rows: list, filepath: str, start_date, end_date):
    c = canvas.Canvas(filepath, pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, h - 50, "Attendance Report")
    c.setFont("Helvetica", 10)
    c.drawString(50, h - 68, f"Period: {start_date}  to  {end_date}")
    c.line(50, h - 78, w - 50, h - 78)

    headers  = ["User ID", "Name", "Date", "Entry", "Exit", "Status"]
    col_x    = [50, 110, 260, 340, 410, 480]
    y = h - 100
    c.setFont("Helvetica-Bold", 9)
    for i, hdr in enumerate(headers):
        c.drawString(col_x[i], y, hdr)
    y -= 16
    c.setFont("Helvetica", 9)
    for row in rows:
        if y < 60:
            c.showPage(); y = h - 50; c.setFont("Helvetica", 9)
        for i, val in enumerate([
            row["user_id"], row["name"][:22], row["date"],
            row["entry"], row["exit"], row["status"]
        ]):
            c.drawString(col_x[i], y, str(val))
        y -= 14
    c.save()
    logger.info(f"Attendance PDF: {filepath}")


# ── Revenue report ────────────────────────────────────────────────────────────

def get_revenue_report() -> list:
    session  = get_session()
    students = session.query(Student).all()
    result   = []
    for s in students:
        total_fee  = sum(sub.total_fee for sub in s.subscriptions)
        total_paid = sum(p.amount_paid for p in s.payments)
        balance    = total_fee - total_paid
        result.append({
            "user_id":   s.user_id,
            "name":      s.name,
            "class":     s.class_.name if s.class_ else "—",
            "total_fee": total_fee,
            "paid":      total_paid,
            "balance":   balance,
            "status": (
                "Paid"    if total_fee > 0 and total_paid >= total_fee else
                "Partial" if total_paid > 0 else
                "Unpaid"
            ),
        })
    session.close()
    return result


def export_revenue_excel(rows: list, filepath: str):
    pd.DataFrame(rows).to_excel(filepath, index=False)


def export_revenue_pdf(rows: list, filepath: str):
    c = canvas.Canvas(filepath, pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, h - 50, "Revenue Report")
    c.line(50, h - 62, w - 50, h - 62)
    headers = ["User ID", "Name", "Class", "Total Fee", "Paid", "Balance", "Status"]
    col_x   = [50, 110, 230, 310, 380, 440, 505]
    y = h - 80
    c.setFont("Helvetica-Bold", 9)
    for i, hdr in enumerate(headers):
        c.drawString(col_x[i], y, hdr)
    y -= 16
    c.setFont("Helvetica", 9)
    for row in rows:
        if y < 60:
            c.showPage(); y = h - 50; c.setFont("Helvetica", 9)
        for i, val in enumerate([
            row["user_id"], row["name"][:20], row["class"][:12],
            f"{row['total_fee']:,.0f}", f"{row['paid']:,.0f}",
            f"{row['balance']:,.0f}", row["status"]
        ]):
            c.drawString(col_x[i], y, str(val))
        y -= 14
    c.save()
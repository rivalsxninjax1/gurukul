from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from database.connection import get_session
from models.subscription import StudentSubscription, SubscriptionPayment
from models.student import Student
from utils.bs_converter import days_remaining_label, bs_str
from services.attendance_analytics_service import (
    get_two_month_analytics, bs_month_name
)
from services.exam_service import get_results_for_student
import logging

logger = logging.getLogger(__name__)

CENTRE_NAME = "GURUKUL ACADEMY AND TUITION CENTRE"


def create_subscription(student_id: int, start_date: date,
                         duration_months: int, total_fee: float) -> int:
    end_date = start_date + relativedelta(months=duration_months)
    session  = get_session()
    active = session.query(StudentSubscription).filter_by(
        student_id=student_id, status="active"
    ).all()
    for sub in active:
        sub.status = "expired"
    new_sub = StudentSubscription(
        student_id = student_id,
        start_date = start_date,
        end_date   = end_date,
        total_fee  = total_fee,
        status     = "active",
    )
    session.add(new_sub)
    session.commit()
    sid = new_sub.id
    session.close()
    return sid


def renew_subscription(student_id: int, start_date: date,
                        duration_months: int, total_fee: float,
                        carry_forward_due: bool = False) -> int:
    if carry_forward_due:
        sub = get_active_subscription(student_id)
        if sub and sub["balance"] > 0:
            total_fee += sub["balance"]
    return create_subscription(student_id, start_date,
                                duration_months, total_fee)


def get_active_subscription(student_id: int) -> dict | None:
    session = get_session()
    today   = date.today()
    sub = session.query(StudentSubscription).filter_by(
        student_id=student_id, status="active"
    ).order_by(StudentSubscription.start_date.desc()).first()
    if not sub:
        session.close()
        return None
    if sub.end_date < today:
        sub.status = "expired"
        session.commit()
        session.close()
        return None
    total_paid = sum(p.amount_paid for p in sub.payments)
    pay_status = (
        "paid"    if total_paid >= sub.total_fee else
        "partial" if total_paid > 0 else
        "unpaid"
    )
    result = {
        "id":         sub.id,
        "start_date": sub.start_date,
        "end_date":   sub.end_date,
        "total_fee":  sub.total_fee,
        "total_paid": total_paid,
        "balance":    sub.total_fee - total_paid,
        "days_left":  (sub.end_date - today).days,
        "days_label": days_remaining_label(sub.end_date),
        "pay_status": pay_status,
    }
    session.close()
    return result


def get_subscription_history(student_id: int) -> list:
    session = get_session()
    subs = session.query(StudentSubscription).filter_by(
        student_id=student_id
    ).order_by(StudentSubscription.start_date.desc()).all()
    result = []
    for sub in subs:
        total_paid = sum(p.amount_paid for p in sub.payments)
        balance    = sub.total_fee - total_paid
        result.append({
            "id":          sub.id,
            "start_date":  sub.start_date,
            "end_date":    sub.end_date,
            "total_fee":   sub.total_fee,
            "total_paid":  total_paid,
            "balance":     balance,
            "status":      sub.status,
            "days_label":  days_remaining_label(sub.end_date),
            "pay_status":  (
                "paid"    if total_paid >= sub.total_fee else
                "partial" if total_paid > 0 else
                "unpaid"
            ),
        })
    session.close()
    return result


def get_outstanding_balance(student_id: int) -> float:
    session = get_session()
    subs    = session.query(StudentSubscription).filter_by(
        student_id=student_id
    ).all()
    total = sum(
        max(0, sub.total_fee - sum(p.amount_paid for p in sub.payments))
        for sub in subs
    )
    session.close()
    return total


def get_payments_for_subscription(subscription_id: int) -> list:
    session = get_session()
    pays = session.query(SubscriptionPayment).filter_by(
        subscription_id=subscription_id
    ).order_by(SubscriptionPayment.payment_date.desc()).all()
    result = [{
        "id":     p.id,
        "date":   p.payment_date,
        "amount": p.amount_paid,
        "method": p.payment_method,
        "note":   p.note or "",
    } for p in pays]
    session.close()
    return result


def get_all_payments_for_student(student_id: int) -> list:
    session = get_session()
    pays = session.query(SubscriptionPayment).filter_by(
        student_id=student_id
    ).order_by(SubscriptionPayment.payment_date.desc()).all()
    result = [{
        "id":     p.id,
        "date":   p.payment_date,
        "amount": p.amount_paid,
        "method": p.payment_method,
        "note":   p.note or "",
        "sub_id": p.subscription_id,
    } for p in pays]
    session.close()
    return result


def add_payment(student_id: int, subscription_id: int,
                amount: float, method: str,
                note: str, payment_date: date) -> int:
    session = get_session()
    p = SubscriptionPayment(
        student_id      = student_id,
        subscription_id = subscription_id,
        amount_paid     = amount,
        payment_date    = payment_date,
        payment_method  = method,
        note            = note,
    )
    session.add(p)
    session.commit()
    pid = p.id
    session.close()
    return pid


def get_subscription_dashboard_stats() -> dict:
    session      = get_session()
    today        = date.today()
    students     = session.query(Student).all()
    active_count  = 0
    expired_count = 0
    pending_count = 0
    total_revenue = 0.0
    total_pending = 0.0
    for s in students:
        active_subs = [sub for sub in s.subscriptions
                       if sub.status == "active"]
        if not active_subs:
            expired_count += 1
            continue
        sub  = active_subs[-1]
        paid = sum(p.amount_paid for p in sub.payments)
        total_revenue += paid
        balance = sub.total_fee - paid
        if balance > 0:
            total_pending += balance
        if sub.end_date < today:
            sub.status = "expired"
            expired_count += 1
        else:
            active_count += 1
            if balance > 0:
                pending_count += 1
    try:
        session.commit()
    except Exception:
        session.rollback()
    session.close()
    return {
        "active":        active_count,
        "expired":       expired_count,
        "pending":       pending_count,
        "total_revenue": total_revenue,
        "total_pending": total_pending,
    }


def get_student_subscription_flags(student_id: int) -> dict:
    sub = get_active_subscription(student_id)
    if not sub:
        return {
            "flag":       "expired",
            "label":      "Expired",
            "days_label": "No active subscription",
            "pay_status": "—",
            "color":      "#c0392b",
        }
    days     = sub["days_left"]
    pstat    = sub["pay_status"]
    days_lbl = sub["days_label"]
    if days <= 3:
        return {"flag": "expiring_soon",   "label": f"Expiring in {days}d",
                "days_label": days_lbl,    "pay_status": pstat, "color": "#e67e22"}
    if pstat in ("partial", "unpaid"):
        return {"flag": "payment_pending", "label": "Payment Pending",
                "days_label": days_lbl,    "pay_status": pstat, "color": "#d35400"}
    return    {"flag": "active",           "label": f"Active · {days_lbl}",
                "days_label": days_lbl,    "pay_status": pstat, "color": "#27ae60"}


# ── Compact Receipt PDF ───────────────────────────────────────────────────────

def generate_payment_receipt(payment_id: int, output_path: str,
                              centre_name: str = "GURUKUL ACADEMY AND TRAINING CENTER",
                              centre_address: str = "Biratnagar-1, Bhatta Chowk"):
    """
    Compact A6 receipt with PNG logo + full institution branding.
    """
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import A6
    from utils.logo_helper import get_logo_path, logo_exists
    import os

    session = get_session()
    p = session.query(SubscriptionPayment).get(payment_id)
    if not p:
        session.close()
        return

    s        = p.student
    sub      = p.subscription
    sub_paid = sum(x.amount_paid for x in sub.payments) if sub else 0
    bal      = (sub.total_fee - sub_paid) if sub else 0
    pdate    = bs_str(p.payment_date)
    session.close()

    attendance_stats = None
    latest_exam = None
    if s:
        attendance = get_two_month_analytics(s.id, s.join_date)
        if attendance:
            for key in ("current", "previous"):
                stats = attendance.get(key)
                if stats and stats.get("bs_month"):
                    attendance_stats = stats
                    break
        exams = [
            e for e in get_results_for_student(s.id, s.join_date)
            if e["has_results"]
        ]
        if exams:
            latest_exam = exams[0]

    W, H = A6
    c = pdf_canvas.Canvas(output_path, pagesize=A6)

    # ── Header: Logo + Institution name ──────────────────────────────────────
    logo_path  = get_logo_path()
    name_y     = H - 28
    if os.path.isfile(logo_path):
        try:
            logo_h = 36
            logo_w = 36
            # Keep aspect ratio using PIL
            from PIL import Image as PILImage
            with PILImage.open(logo_path) as img:
                iw, ih = img.size
            ratio  = min(logo_w / iw, logo_h / ih)
            draw_w = iw * ratio
            draw_h = ih * ratio
            img_x = (W - draw_w) / 2
            img_y = H - 16 - draw_h
            c.drawImage(
                logo_path,
                img_x,
                img_y,
                width  = draw_w,
                height = draw_h,
                mask   = "auto",
                preserveAspectRatio = True,
            )
            name_y = img_y - 10
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawCentredString(W / 2, name_y, centre_name)

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawCentredString(W / 2, name_y - 13, centre_address)
    c.drawCentredString(W / 2, name_y - 24, "Payment Receipt")

    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(0.5)
    c.line(10, name_y - 32, W - 10, name_y - 32)

    y = name_y - 48
    c.setFillColorRGB(0.1, 0.1, 0.1)

    def line_kv(label, val, bold_val=False):
        nonlocal y
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(12, y, label)
        c.setFont("Helvetica-Bold" if bold_val else "Helvetica", 8)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.drawRightString(W - 12, y, str(val))
        y -= 14

    def section_title(title):
        nonlocal y
        y -= 4
        c.setFont("Helvetica-Bold", 8)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(12, y, title.upper())
        y -= 3
        c.setStrokeColorRGB(0.85, 0.85, 0.85)
        c.line(12, y, W - 12, y)
        y -= 11

    section_title("Student")
    line_kv("Name",    s.name    if s else "—", bold_val=True)
    line_kv("User ID", s.user_id if s else "—")

    section_title("Subscription")
    if sub:
        line_kv("Period", f"{bs_str(sub.start_date)} → {bs_str(sub.end_date)}")
        line_kv("Total Fee", f"Rs. {sub.total_fee:,.0f}")

    section_title("Payment")
    line_kv("Date",   pdate)
    line_kv("Method", p.payment_method)
    if p.note:
        line_kv("Note", p.note)

    if attendance_stats:
        section_title(
            f"Attendance · {bs_month_name(attendance_stats['bs_month'])}"
            f" {attendance_stats.get('bs_year', '')}".strip()
        )
        for label, key in [
            ("Working Days", "working_days"),
            ("Present Days", "present"),
            ("Absent Days", "absent"),
        ]:
            line_kv(label, attendance_stats.get(key, 0))

    if latest_exam:
        section_title(f"Last Exam · {latest_exam['exam']}")
        subjects = latest_exam.get("subjects", [])
        for subj in subjects[:3]:
            marks = "—" if subj["marks"] is None else str(subj["marks"])
            line_kv(subj["subject"], f"{marks} / {subj['full']}")
        if len(subjects) > 3:
            line_kv("More Subjects", "See profile for details")

    # Prominent amount
    y -= 6
    c.setStrokeColorRGB(0.1, 0.1, 0.1)
    c.setLineWidth(1)
    c.line(12, y, W - 12, y)
    y -= 16
    c.setFont("Helvetica-Bold", 13)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(12, y, "Amount Paid")
    c.drawRightString(W - 12, y, f"Rs. {p.amount_paid:,.0f}")
    y -= 4
    c.line(12, y, W - 12, y)
    y -= 14

    if bal > 0:
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.6, 0.2, 0.2)
        c.drawString(12, y, "Remaining Balance")
        c.drawRightString(W - 12, y, f"Rs. {bal:,.0f}")

    # Footer
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.setLineWidth(0.5)
    c.line(12, 28, W - 12, 28)
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.55, 0.55, 0.55)
    c.drawCentredString(W / 2, 18, "Thank you! — Computer generated receipt.")
    c.save()

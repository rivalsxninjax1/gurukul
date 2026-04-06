from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from database.connection import get_session
from models.subscription import StudentSubscription, SubscriptionPayment
from models.student import Student
import logging

logger = logging.getLogger(__name__)


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
    logger.info(f"Subscription {sid} created for student {student_id}")
    return sid


def renew_subscription(student_id: int, start_date: date,
                        duration_months: int, total_fee: float) -> int:
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
    result = {
        "id":         sub.id,
        "start_date": sub.start_date,
        "end_date":   sub.end_date,
        "total_fee":  sub.total_fee,
        "total_paid": total_paid,
        "balance":    sub.total_fee - total_paid,
        "days_left":  (sub.end_date - today).days,
        "pay_status": (
            "paid"    if total_paid >= sub.total_fee else
            "partial" if total_paid > 0 else
            "unpaid"
        ),
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
        result.append({
            "id":         sub.id,
            "start_date": sub.start_date,
            "end_date":   sub.end_date,
            "total_fee":  sub.total_fee,
            "total_paid": total_paid,
            "balance":    sub.total_fee - total_paid,
            "status":     sub.status,
            "pay_status": (
                "paid"    if total_paid >= sub.total_fee else
                "partial" if total_paid > 0 else
                "unpaid"
            ),
        })
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


def get_subscription_dashboard_stats() -> dict:
    session = get_session()
    today   = date.today()
    students = session.query(Student).all()

    active_count  = 0
    expired_count = 0
    pending_count = 0
    total_revenue = 0.0
    total_pending = 0.0

    for s in students:
        subs = [sub for sub in s.subscriptions if sub.status == "active"]
        if not subs:
            expired_count += 1
            continue
        sub  = subs[-1]
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
    today = date.today()
    sub   = get_active_subscription(student_id)
    if not sub:
        return {"flag": "expired", "label": "Expired", "days_left": 0,
                "pay_status": "—", "color": "#c0392b"}
    days  = sub["days_left"]
    pstat = sub["pay_status"]
    if days <= 3:
        return {"flag": "expiring_soon", "label": f"Expiring in {days}d",
                "days_left": days, "pay_status": pstat, "color": "#e67e22"}
    if pstat in ("partial", "unpaid"):
        return {"flag": "payment_pending", "label": "Payment Pending",
                "days_left": days, "pay_status": pstat, "color": "#d35400"}
    return {"flag": "active", "label": f"Active ({days}d left)",
            "days_left": days, "pay_status": pstat, "color": "#27ae60"}


def generate_payment_receipt(payment_id: int, output_path: str):
    """
    PDF receipt for a SINGLE payment.
    Shows ONLY the current subscription details and this payment's impact.
    Does NOT include previous subscriptions or their unpaid amounts.
    """
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import A4
    from utils.bs_converter import bs_str

    session = get_session()
    p = session.query(SubscriptionPayment).get(payment_id)
    if not p:
        session.close()
        return

    s   = p.student
    sub = p.subscription

    # Only sum payments for THIS subscription
    sub_paid = sum(x.amount_paid for x in sub.payments) if sub else 0
    sub_balance = (sub.total_fee - sub_paid) if sub else 0
    created  = str(p.created_at)[:16] if p.created_at else ""
    session.close()

    c = pdf_canvas.Canvas(output_path, pagesize=A4)
    w, h = A4

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, h - 55, "Payment Receipt")
    c.setFont("Helvetica", 10)
    c.drawString(50, h - 72, f"Generated: {created}")
    c.line(50, h - 84, w - 50, h - 84)

    y = h - 112

    def section(title):
        nonlocal y
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, title)
        y -= 6
        c.line(50, y, w - 50, y)
        y -= 16

    def kv(label, val):
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(60,  y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(200, y, str(val))
        y -= 18

    section("Student")
    kv("Name",    s.name    if s else "—")
    kv("User ID", s.user_id if s else "—")
    kv("Phone",   s.phone or "—" if s else "—")
    y -= 8

    section("Subscription")
    if sub:
        kv("Period",    f"{bs_str(sub.start_date)}  to  {bs_str(sub.end_date)}")
        kv("Total Fee", f"Rs. {sub.total_fee:,.0f}")
        kv("Status",    sub.status.capitalize())
    else:
        kv("Subscription", "Not found")
    y -= 8

    section("This Payment")
    kv("Amount Paid",    f"Rs. {p.amount_paid:,.0f}")
    kv("Payment Date",   bs_str(p.payment_date))
    kv("Payment Method", p.payment_method)
    if p.note:
        kv("Note", p.note)
    y -= 8

    section("Balance for This Subscription")
    kv("Total Fee",   f"Rs. {sub.total_fee:,.0f}" if sub else "—")
    kv("Total Paid",  f"Rs. {sub_paid:,.0f}")
    kv("Balance Due", f"Rs. {sub_balance:,.0f}")

    # Footer
    c.line(50, 70, w - 50, 70)
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 56,
                 "This receipt is valid for the current subscription only.")
    c.drawString(50, 44, "Computer-generated. No signature required.")
    c.save()
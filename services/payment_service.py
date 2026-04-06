from database.connection import get_session
from models.payment import Payment
from models.billing import Billing
from datetime import date as date_type
import logging

logger = logging.getLogger(__name__)


def get_student_payment_summary(student_id: int) -> dict:
    """Returns total_fee, total_paid, balance for a student."""
    session = get_session()
    bills    = session.query(Billing).filter_by(student_id=student_id).all()
    payments = session.query(Payment).filter_by(student_id=student_id).all()
    total_fee  = sum(b.amount for b in bills)
    total_paid = sum(p.amount_paid for p in payments)
    session.close()
    return {
        "total_fee":  total_fee,
        "total_paid": total_paid,
        "balance":    total_fee - total_paid,
    }


def add_payment(student_id: int, amount: float,
                method: str, note: str,
                payment_date: date_type) -> Payment:
    session = get_session()
    p = Payment(
        student_id     = student_id,
        amount_paid    = amount,
        payment_date   = payment_date,
        payment_method = method,
        note           = note,
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    pid = p.id
    session.close()
    logger.info(f"Payment {pid} added for student {student_id}: Rs.{amount}")
    return pid


def get_payments_for_student(student_id: int) -> list:
    session = get_session()
    rows = session.query(Payment).filter_by(student_id=student_id)\
                  .order_by(Payment.payment_date.desc()).all()
    result = [
        {
            "id":     r.id,
            "amount": r.amount_paid,
            "date":   str(r.payment_date),
            "method": r.payment_method,
            "note":   r.note or "",
        }
        for r in rows
    ]
    session.close()
    return result
def generate_payment_receipt(payment_id: int, output_path: str):
    """Generate a PDF receipt for a single payment."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    session = get_session()
    p = session.query(Payment).get(payment_id)
    if not p:
        session.close()
        return

    from services.payment_service import get_student_payment_summary
    summary = get_student_payment_summary(p.student_id)
    s       = p.student
    session.close()

    c = canvas.Canvas(output_path, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, h - 55, "Payment Receipt")
    c.setFont("Helvetica", 10)
    c.drawString(50, h - 72, f"Generated: {p.created_at.strftime('%Y-%m-%d %H:%M') if p.created_at else ''}")
    c.line(50, h - 82, w - 50, h - 82)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, h - 106, "Student Information")
    c.setFont("Helvetica", 11)
    details = [
        ("Name",           s.name if s else "—"),
        ("User ID",        s.user_id if s else "—"),
        ("Phone",          s.phone or "—" if s else "—"),
    ]
    y = h - 126
    for label, val in details:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(60,  y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(180, y, str(val))
        y -= 20

    y -= 10
    c.line(50, y, w - 50, y)
    y -= 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Payment Details")
    y -= 20

    pay_details = [
        ("Amount Paid",     f"Rs. {p.amount_paid:,.0f}"),
        ("Payment Date",    str(p.payment_date)),
        ("Payment Method",  p.payment_method),
        ("Note",            p.note or "—"),
    ]
    for label, val in pay_details:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(60,  y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(180, y, str(val))
        y -= 20

    y -= 10
    c.line(50, y, w - 50, y)
    y -= 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Account Summary")
    y -= 20

    summary_rows = [
        ("Total Fee",     f"Rs. {summary['total_fee']:,.0f}"),
        ("Total Paid",    f"Rs. {summary['total_paid']:,.0f}"),
        ("Balance Due",   f"Rs. {summary['balance']:,.0f}"),
    ]
    for label, val in summary_rows:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(60,  y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(180, y, val)
        y -= 20

    c.line(50, 70, w - 50, 70)
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 55, "This is a computer-generated receipt.")
    c.save()
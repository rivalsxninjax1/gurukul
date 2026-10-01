from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from database.connection import get_session
from models.subscription import StudentSubscription, SubscriptionPayment
from models.student import Student
from utils.bs_converter import (
    days_remaining_label, bs_str, ad_to_bs,
    bs_month_end_ad, prorated_fee,
)
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


def get_last_subscription(student_id: int) -> dict | None:
    """Return the most recent subscription for a student regardless of status.

    Unlike get_active_subscription(), this never mutates the subscription
    status and returns even expired records.  Returns None only if the
    student has no subscriptions at all.
    """
    session = get_session()
    sub = session.query(StudentSubscription).filter_by(
        student_id=student_id
    ).order_by(StudentSubscription.start_date.desc()).first()
    if not sub:
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
        "days_label": days_remaining_label(sub.end_date),
        "pay_status": pay_status,
        "status":     sub.status,
    }
    session.close()
    return result


def renew_subscription(student_id: int, start_date: date,
                        duration_months: int, total_fee: float,
                        carry_forward_due: bool = False) -> int:
    if carry_forward_due:
        # Use last subscription (active OR expired) so carry-forward works
        # even when the student's subscription has already expired.
        sub = get_active_subscription(student_id) or get_last_subscription(student_id)
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


def update_subscription_fee(subscription_id: int, new_fee: float) -> bool:
    """Update the total_fee of an existing subscription in place
    (e.g. user-edited price). Returns False if not found."""
    session = get_session()
    sub = session.query(StudentSubscription).get(subscription_id)
    if not sub:
        session.close()
        return False
    sub.total_fee = new_fee
    session.commit()
    session.close()
    logger.info(f"Subscription {subscription_id}: total_fee updated to {new_fee}")
    return True


def update_subscription_dates(subscription_id: int,
                               start_date: date,
                               end_date: date) -> bool:
    """Update the start_date and/or end_date of an existing subscription
    in place (e.g. user-edited subscription period). Returns False if
    not found."""
    session = get_session()
    sub = session.query(StudentSubscription).get(subscription_id)
    if not sub:
        session.close()
        return False
    sub.start_date = start_date
    sub.end_date   = end_date
    session.commit()
    session.close()
    logger.info(
        f"Subscription {subscription_id}: dates updated to "
        f"{start_date} → {end_date}"
    )
    return True


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


def get_student_financial_summary(student_id: int) -> dict:
    """Return total paid and total pending for a student across all their subs."""
    session = get_session()
    subs    = session.query(StudentSubscription).filter_by(
        student_id=student_id
    ).all()
    total_paid    = 0.0
    total_pending = 0.0
    for sub in subs:
        paid     = sum(p.amount_paid for p in sub.payments)
        total_paid    += paid
        total_pending += max(0.0, sub.total_fee - paid)
    session.close()
    return {"paid": total_paid, "pending": total_pending}


def record_deleted_student(student_name: str, student_user_id: str,
                            revenue_preserved: float,
                            pending_written_off: float) -> None:
    """Write a ledger entry before a student is deleted."""
    from models.deleted_ledger import DeletedStudentLedger
    session = get_session()
    session.add(DeletedStudentLedger(
        student_name        = student_name,
        student_user_id     = student_user_id,
        revenue_preserved   = revenue_preserved,
        pending_written_off = pending_written_off,
    ))
    session.commit()
    session.close()


def get_deleted_ledger_totals() -> dict:
    """Return cumulative revenue and pending written off from deleted students."""
    from models.deleted_ledger import DeletedStudentLedger
    session = get_session()
    entries = session.query(DeletedStudentLedger).all()
    revenue = sum(e.revenue_preserved   for e in entries)
    pending = sum(e.pending_written_off for e in entries)
    session.close()
    return {"revenue": revenue, "pending_written_off": pending}


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


def create_initial_subscription(student_id: int, join_date: date,
                                monthly_fee: float,
                                first_start: date | None = None,
                                first_end: date | None = None,
                                first_fee: float | None = None) -> int:
    """Create the FIRST subscription period for a newly registered student.

    * Custom first period (first_start/first_end/first_fee given):
      exactly those dates and that amount are used.
    * Otherwise: join date -> last day of that Nepali month, with the
      monthly fee prorated by number of days (a join on the 1st pays the
      full monthly fee).

    The student's monthly_fee is stored; the automatic subscription starts
    the day after the first period ends and uses the monthly fee.
    """
    if first_start and first_end:
        start, end = first_start, first_end
        fee = float(first_fee if first_fee is not None else 0.0)
    else:
        start = join_date
        end   = bs_month_end_ad(join_date)
        fee   = prorated_fee(monthly_fee, start, end)

    session = get_session()
    student = session.query(Student).get(student_id)
    if student is not None:
        student.monthly_fee = float(monthly_fee)
    sub = StudentSubscription(
        student_id = student_id,
        start_date = start,
        end_date   = end,
        total_fee  = fee,
        status     = "active" if end >= date.today() else "expired",
    )
    session.add(sub)
    session.commit()
    sid = sub.id
    # If the first period is already in the past, catch up right away.
    if end < date.today() and student is not None:
        _chain_renewals(session, student, date.today())
        session.commit()
    session.close()
    return sid


def _chain_renewals(session, student, today: date) -> int:
    """Create every missing Nepali-month period for one student up to today.

    The next period always starts the day after the previous one ended.
    * If that day is the 1st of a Nepali month -> full month, full fee.
    * Otherwise (old students on rolling cycles, or a custom first period
      that stopped mid-month) -> ONE bridge period up to the last day of
      that Nepali month, fee = monthly fee x days / days in month.
    After that every period is a whole Nepali month at the monthly fee.
    """
    last = session.query(StudentSubscription).filter_by(
        student_id=student.id
    ).order_by(StudentSubscription.start_date.desc(),
               StudentSubscription.id.desc()).first()
    if not last:
        return 0

    monthly = student.monthly_fee
    if monthly is None:
        monthly = last.total_fee
        student.monthly_fee = monthly

    created    = 0
    next_start = last.end_date + timedelta(days=1)
    while next_start <= today:
        next_end = bs_month_end_ad(next_start)
        _, _, bs_day = ad_to_bs(next_start)
        fee = float(round(monthly)) if bs_day == 1 else prorated_fee(
            monthly, next_start, next_end
        )
        session.add(StudentSubscription(
            student_id = student.id,
            start_date = next_start,
            end_date   = next_end,
            total_fee  = fee,
            status     = "active" if next_end >= today else "expired",
        ))
        created   += 1
        next_start = next_end + timedelta(days=1)
    return created


def auto_renew_expired_students() -> int:
    """Called once on app startup.

    For every student with no active subscription, keep creating Nepali-
    month periods (1st to last day of the BS month) at the student's
    monthly fee until one covers today.  Old students on rolling cycles
    get a single prorated bridge period first (see _chain_renewals).

    Outstanding balances stay on their own periods and are shown via
    get_outstanding_balance() — they are never added into a new fee.

    Returns the total number of subscriptions auto-created.
    """
    session = get_session()
    today   = date.today()

    stale = session.query(StudentSubscription).filter(
        StudentSubscription.status == "active",
        StudentSubscription.end_date < today,
    ).all()
    for s in stale:
        s.status = "expired"
    if stale:
        session.commit()

    created = 0
    for student in session.query(Student).all():
        active = session.query(StudentSubscription).filter_by(
            student_id=student.id, status="active"
        ).first()
        if active:
            continue
        created += _chain_renewals(session, student, today)
        session.commit()

    session.close()
    logger.info(f"auto_renew_expired_students: {created} subscription(s) created.")
    return created


def get_subscription_dashboard_stats() -> dict:
    """Calculate dashboard statistics.

    Pending / Outstanding includes balances from ALL subscriptions
    (active and expired) where the student still owes money.
    Total Revenue only counts actual payments received.
    """
    session      = get_session()
    today        = date.today()
    students     = session.query(Student).all()
    active_count  = 0
    expired_count = 0
    pending_count = 0
    total_revenue = 0.0
    total_pending = 0.0

    for s in students:
        subs = s.subscriptions
        if not subs:
            continue

        # Mark any active sub that has passed its end_date as expired
        has_active = False
        for sub in subs:
            paid = sum(p.amount_paid for p in sub.payments)
            total_revenue += paid

            # Include outstanding balance from EVERY subscription
            # (active OR expired) — unpaid dues don't disappear on expiry
            balance = max(0.0, sub.total_fee - paid)
            if balance > 0:
                total_pending += balance

            if sub.status == "active":
                if sub.end_date < today:
                    sub.status = "expired"
                else:
                    has_active = True

        if has_active:
            active_count += 1
            # Count as payment-pending if active sub has unpaid balance
            active_subs = [sub for sub in subs if sub.status == "active"]
            if active_subs:
                active_sub = active_subs[-1]
                active_paid = sum(p.amount_paid for p in active_sub.payments)
                if active_sub.total_fee - active_paid > 0:
                    pending_count += 1
        else:
            expired_count += 1
            # Student has outstanding on expired subs — count as pending
            total_owed = sum(
                max(0.0, sub.total_fee - sum(p.amount_paid for p in sub.payments))
                for sub in subs
            )
            if total_owed > 0:
                pending_count += 1

    try:
        session.commit()
    except Exception:
        session.rollback()
    session.close()

    # Add revenue from deleted students; subtract their written-off pending
    ledger = get_deleted_ledger_totals()
    total_revenue += ledger["revenue"]
    total_pending -= ledger["pending_written_off"]
    if total_pending < 0:
        total_pending = 0.0

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
    Compact receipt with PNG logo + full institution branding.
    Uses A6 width with dynamic height so exam results never overflow.
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
    class_name = s.class_.name if (s and s.class_) else "—"
    group_name = s.group.name  if (s and s.group)  else "—"
    session.close()

    attendance_months = []      # up to two months, most recent first
    latest_exam = None
    if s:
        attendance = get_two_month_analytics(s.id, s.join_date)
        for key in ("current", "previous"):
            stats = (attendance or {}).get(key)
            if stats and stats.get("bs_month"):
                attendance_months.append(stats)
        exams = [
            e for e in get_results_for_student(s.id, s.join_date)
            if e["has_results"]
        ]
        if exams:
            latest_exam = exams[0]

    A6_W, A6_H = A6
    W = A6_W

    # ── Pre-calculate total content height so canvas is never clipped ─────────
    # Each section_title ≈ 18 pts, each line_kv ≈ 14 pts
    SECTION_H = 18
    KV_H      = 14
    HEADER_H  = 36 + 10 + 13 + 13 + 12 + 16 + 20  # logo + name + addr + "Receipt" + rule + gap

    n_rows = 2          # student: name + user_id
    n_rows += 2         # class + group
    n_rows += 2 + (1 if p.note else 0)  # payment: date + method + optional note
    n_sections = 3

    # Attendance: one compact line per month (always shown)
    n_rows += max(1, len(attendance_months))
    n_sections += 1

    exam_subj_count = 0
    if latest_exam:
        subjects = latest_exam.get("subjects", [])
        exam_subj_count = min(len(subjects), 3)
        if len(subjects) > 3:
            exam_subj_count += 1   # "More subjects" line
        n_rows += exam_subj_count
        n_sections += 1

    AMOUNT_H  = 6 + 16 + 4 + 14   # separator + bold amount + line + balance row
    FOOTER_H  = 30

    total_h = HEADER_H + (n_sections * SECTION_H) + (n_rows * KV_H) + AMOUNT_H + FOOTER_H + 20
    # Never smaller than A6
    H = max(A6_H, total_h)

    c = pdf_canvas.Canvas(output_path, pagesize=(W, H))

    # ── Header: Logo + Institution name ──────────────────────────────────────
    logo_path  = get_logo_path()
    name_y     = H - 28
    if os.path.isfile(logo_path):
        try:
            logo_h = 36
            logo_w = 36
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

    section_title("Class & Group")
    line_kv("Class", class_name, bold_val=True)
    line_kv("Group", group_name, bold_val=True)

    section_title("Payment")
    line_kv("Date",   pdate)
    line_kv("Method", p.payment_method)
    if p.note:
        line_kv("Note", p.note)

    section_title("Attendance")
    shown = [m for m in attendance_months if m.get("working_days")]
    if not shown:
        line_kv("Status", "No attendance recorded")
    for st in shown:
        month_label = f"{bs_month_name(st['bs_month'])} {st.get('bs_year', '')}"
        line_kv(
            month_label,
            f"Present {st.get('present', 0)} · Absent {st.get('absent', 0)}"
            f" · of {st.get('working_days', 0)} days",
        )

    if latest_exam:
        section_title(f"Last Exam · {latest_exam['exam']}")
        subjects = latest_exam.get("subjects", [])
        for subj in subjects[:3]:
            marks = "—" if subj["marks"] is None else str(subj["marks"])
            line_kv(subj["subject"], f"{marks} / {subj['full']}")
        if len(subjects) > 3:
            line_kv("More Subjects", "See full profile for details")

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


def generate_payment_receipt_image(
        payment_id: int, output_path: str,
        centre_name: str = "GURUKUL ACADEMY AND TRAINING CENTER",
        centre_address: str = "Biratnagar-1, Bhatta Chowk") -> bool:
    """Generate the payment receipt as a single PNG image (same A6 layout
    as generate_payment_receipt, rasterized to a PNG so it can be placed
    onto other documents or combined on one printed sheet)."""
    import tempfile
    import os
    from utils.pdf_to_image import pdf_first_page_to_png

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_path = tmp.name
    tmp.close()
    try:
        generate_payment_receipt(payment_id, tmp_path, centre_name, centre_address)
        ok = pdf_first_page_to_png(tmp_path, output_path, dpi=300)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    if ok:
        logger.info(f"Payment receipt image: {output_path}")
    return ok

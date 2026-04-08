"""
Unified print/export service.
Generates HTML content for both printing and PDF for:
  - Student Profile
  - Payment Receipt

The SAME HTML is used for both print and PDF — single source of truth.

Usage:
    from services.print_service import (
        get_student_profile_html,
        get_receipt_html,
        print_html,
        html_to_pdf,
    )
"""

import os
import datetime
from utils.bs_converter import bs_str, today_bs
from utils.logo_helper import get_logo_path

CENTRE_NAME    = "GURUKUL ACADEMY AND TRAINING CENTER"
CENTRE_ADDRESS = "Biratnagar-1, Bhatta Chowk"


# ── Logo helper ───────────────────────────────────────────────────────────────

def _logo_html(size: int = 60) -> str:
    """
    Return an <img> tag if logo.png exists, else a styled 'G' circle.
    Uses base64-encoded image so HTML works without external files.
    """
    path = get_logo_path()
    if os.path.isfile(path):
        try:
            import base64
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return (
                f'<img src="data:image/png;base64,{b64}" '
                f'width="{size}" height="{size}" '
                f'style="object-fit:contain;border-radius:50%;" />'
            )
        except Exception:
            pass
    # Fallback: circle with "G"
    fs = int(size * 0.45)
    return (
        f'<div style="display:inline-block;width:{size}px;height:{size}px;'
        f'background:#1a1a1a;border-radius:50%;text-align:center;'
        f'line-height:{size}px;color:#ffffff;font-size:{fs}px;'
        f'font-weight:bold;">G</div>'
    )


# ── Shared header ─────────────────────────────────────────────────────────────

def _header_html(subtitle: str = "") -> str:
    return f"""
    <div style="text-align:center;border-bottom:2px solid #1a1a1a;
                padding-bottom:12px;margin-bottom:16px;">
        {_logo_html(56)}
        <div style="font-size:16px;font-weight:bold;color:#1a1a1a;
                    margin-top:8px;">{CENTRE_NAME}</div>
        <div style="font-size:12px;color:#555555;">{CENTRE_ADDRESS}</div>
        {"" if not subtitle else
         f'<div style="font-size:13px;color:#333333;margin-top:4px;">'
         f'{subtitle}</div>'}
    </div>
    """


# ── Base CSS ──────────────────────────────────────────────────────────────────

_BASE_CSS = """
    * { box-sizing: border-box; }
    body {
        font-family: Arial, sans-serif;
        font-size: 13px;
        color: #1a1a1a;
        margin: 0;
        padding: 16px;
        background: #ffffff;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 12px;
    }
    th {
        background: #2c2c2c;
        color: #ffffff;
        padding: 7px 10px;
        text-align: left;
        font-size: 12px;
    }
    td {
        padding: 6px 10px;
        border-bottom: 1px solid #eeeeee;
        vertical-align: top;
    }
    tr:nth-child(even) td { background: #f7f7f7; }
    .section-title {
        font-size: 11px;
        font-weight: bold;
        color: #888888;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin: 16px 0 6px 0;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 4px;
    }
    .kv-table td.key {
        font-weight: bold;
        color: #555555;
        width: 160px;
        border-bottom: 1px solid #eeeeee;
    }
    .kv-table td.val {
        color: #1a1a1a;
        border-bottom: 1px solid #eeeeee;
    }
    .badge-pass  { color:#1a5c1a; background:#e6f4e6;
                   padding:2px 8px; border-radius:4px; }
    .badge-fail  { color:#8b0000; background:#fdeaea;
                   padding:2px 8px; border-radius:4px; }
    .badge-paid  { color:#1a5c1a; background:#e6f4e6;
                   padding:2px 8px; border-radius:4px; }
    .badge-part  { color:#7a4f00; background:#fdf3e0;
                   padding:2px 8px; border-radius:4px; }
    .badge-unpaid{ color:#8b0000; background:#fdeaea;
                   padding:2px 8px; border-radius:4px; }
    .footer {
        margin-top: 24px;
        border-top: 1px solid #cccccc;
        padding-top: 8px;
        font-size: 10px;
        color: #888888;
        text-align: center;
    }
    .amount-row {
        font-size: 16px;
        font-weight: bold;
        color: #1a1a1a;
        border-top: 2px solid #1a1a1a;
        border-bottom: 2px solid #1a1a1a;
        padding: 8px 10px;
    }
    .warning { color:#8b0000; font-weight:bold; }
"""


# ── Student Profile HTML ──────────────────────────────────────────────────────

def get_student_profile_html(student_id: int) -> str:
    """
    Generate complete HTML for a student profile.
    Used by BOTH print and PDF export — single source of truth.
    """
    from database.connection import get_session
    from models.student import Student
    from services.subscription_service import (
        get_active_subscription, get_subscription_history,
        get_all_payments_for_student, get_outstanding_balance,
    )
    from services.attendance_analytics_service import (
        get_two_month_analytics, bs_month_name
    )
    from services.exam_service import get_results_for_student

    session = get_session()
    s = session.query(Student).get(student_id)
    if not s:
        session.close()
        return "<html><body><p>Student not found.</p></body></html>"

    # Personal details
    name     = s.name
    uid      = s.user_id
    phone    = s.phone or "—"
    guardian = s.guardian_name or "—"
    whatsapp = s.whatsapp_number or "—"
    address  = s.address or "—"
    dob      = bs_str(s.dob)       if s.dob       else "—"
    joined   = bs_str(s.join_date) if s.join_date else "—"
    cls      = s.class_.name if s.class_ else "—"
    grp      = s.group.name  if s.group  else "—"
    join_date_ad = s.join_date

    # Attendance (filtered from join date)
    atts = sorted(
        [a for a in s.attendances
         if (join_date_ad is None or a.date >= join_date_ad)],
        key=lambda a: a.date, reverse=True
    )
    session.close()

    sub         = get_active_subscription(student_id)
    outstanding = get_outstanding_balance(student_id)
    analytics   = get_two_month_analytics(student_id, join_date_ad)
    sub_history = get_subscription_history(student_id)
    payments    = get_all_payments_for_student(student_id)
    exam_data   = [e for e in get_results_for_student(student_id)
                   if e["has_results"]]

    # ── Build HTML ────────────────────────────────────────────────────────────
    h = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>{_BASE_CSS}</style>
</head>
<body>

{_header_html("Student Profile")}
"""

    # Outstanding balance warning
    if outstanding > 0:
        h += f"""
<div class="warning" style="background:#fdeaea;border:1px solid #f5b8b8;
     border-radius:5px;padding:8px 12px;margin-bottom:12px;">
  ⚠ Outstanding balance across all subscriptions: Rs. {outstanding:,.0f}
</div>
"""

    # Personal details
    h += '<div class="section-title">Personal Details</div>'
    h += '<table class="kv-table"><tbody>'
    for k, v in [
        ("User ID",         uid),
        ("Full Name",       name),
        ("Phone",           phone),
        ("Guardian",        guardian),
        ("WhatsApp",        whatsapp),
        ("Address",         address),
        ("Date of Birth",   dob),
        ("Join Date (BS)",  joined),
        ("Class",           cls),
        ("Group",           grp),
    ]:
        h += f'<tr><td class="key">{k}</td><td class="val">{v}</td></tr>'
    h += "</tbody></table>"

    # Active subscription
    h += '<div class="section-title">Active Subscription</div>'
    if sub:
        pay_badge = (
            '<span class="badge-paid">Paid</span>'     if sub["pay_status"] == "paid"    else
            '<span class="badge-part">Partial</span>'  if sub["pay_status"] == "partial" else
            '<span class="badge-unpaid">Unpaid</span>'
        )
        h += '<table class="kv-table"><tbody>'
        for k, v in [
            ("Period (BS)",
             f"{bs_str(sub['start_date'])} → {bs_str(sub['end_date'])}"),
            ("Days",     sub["days_label"]),
            ("Total Fee",f"Rs. {sub['total_fee']:,.0f}"),
            ("Paid",     f"Rs. {sub['total_paid']:,.0f}"),
            ("Balance",  f"Rs. {sub['balance']:,.0f}"),
            ("Status",   pay_badge),
        ]:
            h += f'<tr><td class="key">{k}</td><td class="val">{v}</td></tr>'
        h += "</tbody></table>"
    else:
        h += "<p style='color:#888888;'>No active subscription.</p>"

    # Monthly attendance analytics
    h += '<div class="section-title">Monthly Attendance Analytics</div>'
    h += """
<table>
<thead><tr>
  <th>BS Month</th><th>Working Days</th><th>Present</th>
  <th>Absent</th><th>Incomplete</th><th>Holiday</th>
</tr></thead><tbody>
"""
    for period_key in ("current", "previous"):
        d = analytics[period_key]
        h += (
            f"<tr><td>{bs_month_name(d['bs_month'])} {d['bs_year']}</td>"
            f"<td>{d['working_days']}</td>"
            f"<td>{d['present']}</td>"
            f"<td>{d['absent']}</td>"
            f"<td>{d['incomplete']}</td>"
            f"<td>{d['holiday']}</td></tr>"
        )
    h += "</tbody></table>"

    # Exam results
    if exam_data:
        h += '<div class="section-title">Examination Results</div>'
        for exam in exam_data:
            h += (
                f"<div style='font-weight:bold;margin:8px 0 4px 0;'>"
                f"{exam['exam']}  "
                f"<span style='font-weight:normal;color:#555555;'>"
                f"{exam['percentage']}% "
                f"({exam['total_scored']:.0f}/{exam['total_full']:.0f})"
                f"</span></div>"
            )
            h += "<table><thead><tr>"
            for col in ["Subject", "Full", "Pass", "Obtained", "Result"]:
                h += f"<th>{col}</th>"
            h += "</tr></thead><tbody>"
            for sub_r in exam["subjects"]:
                result = (
                    '<span class="badge-pass">Pass</span>'
                    if sub_r["passed"] is True else
                    '<span class="badge-fail">Fail</span>'
                    if sub_r["passed"] is False else "—"
                )
                marks = str(sub_r["marks"]) if sub_r["marks"] is not None else "—"
                h += (
                    f"<tr>"
                    f"<td>{sub_r['subject']}</td>"
                    f"<td>{sub_r['full']}</td>"
                    f"<td>{sub_r['pass']}</td>"
                    f"<td>{marks}</td>"
                    f"<td>{result}</td>"
                    f"</tr>"
                )
            h += "</tbody></table>"

    # Subscription history
    h += '<div class="section-title">Subscription History</div>'
    h += "<table><thead><tr>"
    for col in ["Start (BS)", "End (BS)", "Fee", "Paid", "Balance", "Status", "Days"]:
        h += f"<th>{col}</th>"
    h += "</tr></thead><tbody>"
    for sh in sub_history:
        sd = sh["start_date"]; ed = sh["end_date"]
        h += (
            f"<tr>"
            f"<td>{bs_str(sd) if hasattr(sd,'year') else sd}</td>"
            f"<td>{bs_str(ed) if hasattr(ed,'year') else ed}</td>"
            f"<td>Rs.{sh['total_fee']:,.0f}</td>"
            f"<td>Rs.{sh['total_paid']:,.0f}</td>"
            f"<td>Rs.{sh['balance']:,.0f}</td>"
            f"<td>{sh['status'].capitalize()}</td>"
            f"<td>{sh['days_label']}</td>"
            f"</tr>"
        )
    h += "</tbody></table>"

    # Payment history
    h += '<div class="section-title">Payment History</div>'
    h += "<table><thead><tr>"
    for col in ["Date (BS)", "Amount", "Method", "Note"]:
        h += f"<th>{col}</th>"
    h += "</tr></thead><tbody>"
    for pay in payments:
        d = pay["date"]
        d_str = bs_str(d) if hasattr(d, "year") else str(d)
        h += (
            f"<tr>"
            f"<td>{d_str}</td>"
            f"<td>Rs.{pay['amount']:,.0f}</td>"
            f"<td>{pay['method']}</td>"
            f"<td>{pay['note'] or ''}</td>"
            f"</tr>"
        )
    h += "</tbody></table>"

    # Footer
    h += f"""
<div class="footer">
  Generated: {today_bs()}  ·  {CENTRE_NAME}  ·  {CENTRE_ADDRESS}
</div>
</body></html>
"""
    return h


# ── Receipt HTML ──────────────────────────────────────────────────────────────

def get_receipt_html(payment_id: int) -> str:
    """
    Generate compact receipt HTML.
    Used by BOTH print and PDF export — single source of truth.
    Does NOT include 'Balance for This Subscription' section.
    """
    from database.connection import get_session
    from models.subscription import SubscriptionPayment

    session = get_session()
    p = session.query(SubscriptionPayment).get(payment_id)
    if not p:
        session.close()
        return "<html><body><p>Receipt not found.</p></body></html>"

    s        = p.student
    sub      = p.subscription
    sub_paid = sum(x.amount_paid for x in sub.payments) if sub else 0
    bal      = max(0, sub.total_fee - sub_paid) if sub else 0
    pdate    = bs_str(p.payment_date)
    created  = str(p.created_at)[:16] if p.created_at else today_bs()
    session.close()

    h = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
{_BASE_CSS}
body {{ max-width: 400px; margin: 0 auto; padding: 16px; }}
</style>
</head>
<body>

{_header_html("Payment Receipt")}

<div class="section-title">Student</div>
<table class="kv-table"><tbody>
  <tr><td class="key">Name</td>
      <td class="val"><strong>{s.name if s else '—'}</strong></td></tr>
  <tr><td class="key">User ID</td>
      <td class="val">{s.user_id if s else '—'}</td></tr>
  <tr><td class="key">Phone</td>
      <td class="val">{s.phone or '—' if s else '—'}</td></tr>
</tbody></table>

<div class="section-title">Subscription</div>
<table class="kv-table"><tbody>
"""
    if sub:
        h += f"""
  <tr><td class="key">Period (BS)</td>
      <td class="val">{bs_str(sub.start_date)} → {bs_str(sub.end_date)}</td></tr>
  <tr><td class="key">Total Fee</td>
      <td class="val">Rs. {sub.total_fee:,.0f}</td></tr>
  <tr><td class="key">Status</td>
      <td class="val">{sub.status.capitalize()}</td></tr>
"""
    else:
        h += '<tr><td colspan="2">Subscription not found.</td></tr>'

    h += f"""
</tbody></table>

<div class="section-title">Payment</div>
<table class="kv-table"><tbody>
  <tr><td class="key">Date (BS)</td>
      <td class="val">{pdate}</td></tr>
  <tr><td class="key">Method</td>
      <td class="val">{p.payment_method}</td></tr>
"""
    if p.note:
        h += f'<tr><td class="key">Note</td><td class="val">{p.note}</td></tr>'

    h += f"""
</tbody></table>

<table style="margin-top:12px;">
<tr class="amount-row">
  <td style="width:60%">Amount Paid</td>
  <td style="text-align:right;font-size:18px;">Rs. {p.amount_paid:,.0f}</td>
</tr>
</table>
"""

    if bal > 0:
        h += f"""
<table>
<tr>
  <td style="color:#8b0000;font-weight:bold;">Remaining Balance</td>
  <td style="text-align:right;color:#8b0000;font-weight:bold;">
      Rs. {bal:,.0f}
  </td>
</tr>
</table>
"""

    h += f"""
<div class="footer">
  Generated: {created}  ·  Computer generated receipt.<br/>
  {CENTRE_NAME}  ·  {CENTRE_ADDRESS}
</div>
</body></html>
"""
    return h


# ── Print action ──────────────────────────────────────────────────────────────

def print_html(html: str, parent=None,
               dialog_title: str = "Print") -> bool:
    """
    Open the native system print dialog and print the given HTML.
    Returns True if user confirmed print, False if cancelled.

    Uses: QPrinter + QPrintDialog + QTextDocument
    Works on Mac and Windows — no PDF file created.
    """
    from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
    from PyQt5.QtGui import QTextDocument
    from PyQt5.QtCore import Qt

    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageSize(QPrinter.A4)
    printer.setColorMode(QPrinter.Color)

    dialog = QPrintDialog(printer, parent)
    dialog.setWindowTitle(dialog_title)

    if dialog.exec_() != QPrintDialog.Accepted:
        return False

    doc = QTextDocument()
    doc.setHtml(html)
    doc.print_(printer)
    return True


def print_receipt_compact(html: str, parent=None) -> bool:
    """
    Print receipt with smaller page size for thermal/receipt printers.
    Falls back to A4 if custom size not available.
    """
    from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
    from PyQt5.QtGui import QTextDocument
    from PyQt5.QtCore import QSizeF, Qt
    from PyQt5.QtCore import QMarginsF

    printer = QPrinter(QPrinter.HighResolution)
    printer.setColorMode(QPrinter.Color)

    # Try to set a compact page size (A6 / receipt size)
    try:
        from PyQt5.QtGui import QPageSize
        from PyQt5.QtCore import QSizeF
        printer.setPageSize(QPrinter.A6)
    except Exception:
        printer.setPageSize(QPrinter.A4)

    dialog = QPrintDialog(printer, parent)
    dialog.setWindowTitle("Print Receipt")

    if dialog.exec_() != QPrintDialog.Accepted:
        return False

    doc = QTextDocument()
    doc.setHtml(html)
    doc.print_(printer)
    return True


# ── PDF export (existing logic wrapper) ──────────────────────────────────────

def html_to_pdf(html: str, output_path: str) -> bool:
    """
    Convert HTML to PDF using reportlab.
    Fallback: use Qt's PDF printer if reportlab fails.
    Returns True on success.
    """
    # Primary: Qt PDF printer (most reliable for HTML)
    try:
        from PyQt5.QtPrintSupport import QPrinter
        from PyQt5.QtGui import QTextDocument

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(output_path)
        printer.setPageSize(QPrinter.A4)
        printer.setColorMode(QPrinter.Color)

        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(
            f"html_to_pdf failed: {e}"
        )
        return False
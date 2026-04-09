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
from utils.bs_converter import bs_str, today_bs, ad_to_bs
from utils.logo_helper import get_logo_path

CENTRE_NAME    = "GURUKUL ACADEMY AND TRAINING CENTER"
CENTRE_ADDRESS = "Biratnagar-1, Bhatta Chowk"

_STATUS_CLASS = {
    "Present": "status-present",
    "Incomplete": "status-incomplete",
    "Absent": "status-absent",
}


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

def _header_html(subtitle: str = "",
                 centre_name: str | None = None,
                 centre_address: str | None = None) -> str:
    subtitle_html = (
        f'<div class="header-subtitle">{subtitle}</div>'
        if subtitle else ""
    )
    centre_name = centre_name or CENTRE_NAME
    centre_address = centre_address or CENTRE_ADDRESS
    return f"""
    <div class="header-block">
        <div class="header-logo">{_logo_html(60)}</div>
        <div class="header-meta">
            <div class="header-name">{centre_name}</div>
            <div class="header-address">{centre_address}</div>
            {subtitle_html}
        </div>
    </div>
    """


def _status_badge_html(status: str | None) -> str:
    if not status:
        return "—"
    css = _STATUS_CLASS.get(status, "")
    extra = f" {css}" if css else ""
    return f'<span class="status-badge{extra}">{status}</span>'


# ── Base CSS ──────────────────────────────────────────────────────────────────


_BASE_CSS = """
    @page { size: A4; margin: 10mm 12mm 12mm 12mm; }
    * { box-sizing: border-box; }
    body {
        font-family: "Helvetica Neue", "Segoe UI", Arial, sans-serif;
        font-size: 12.2px;
        line-height: 1.45;
        color: #0f172a;
        margin: 0;
        padding: 0;
        background: #f3f5fb;
    }
    .doc-container {
        max-width: 720px;
        margin: 0 auto;
        padding: 18px 24px 22px 24px;
        background: #ffffff;
        border-radius: 18px;
        border: 1px solid #e2e7f2;
    }
    .doc-container.compact {
        max-width: 520px;
        padding: 16px 22px 20px 22px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 10px;
        page-break-inside: avoid;
    }
    thead { display: table-header-group; }
    tr { page-break-inside: avoid; }
    th {
        background: #101a46;
        color: #ffffff;
        padding: 6px 10px;
        text-align: left;
        font-size: 11px;
        letter-spacing: 0.3px;
    }
    td {
        padding: 6px 10px;
        border-bottom: 1px solid #ebedf5;
        vertical-align: top;
        font-size: 11px;
        color: #1b2552;
    }
    tr:nth-child(even) td { background: #f8f9ff; }
    .kv-table td.key {
        font-weight: 600;
        color: #5c6483;
        width: 45%;
        border-bottom: 1px solid #edf0f8;
        background: #f7f8fe;
        padding: 6px 10px;
    }
    .kv-table td.val {
        color: #10163a;
        border-bottom: 1px solid #edf0f8;
        background: #ffffff;
        padding: 6px 10px;
    }
    .header-block {
        display: flex;
        align-items: center;
        gap: 14px;
        border-bottom: 1px solid #dfe4f2;
        padding-bottom: 10px;
        margin-bottom: 12px;
    }
    .header-logo { flex-shrink: 0; }
    .header-meta { display: flex; flex-direction: column; gap: 3px; }
    .header-name {
        font-size: 26px;
        font-weight: 800;
        color: #040a27;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        line-height: 1.05;
    }
    .header-address {
        font-size: 12px;
        color: #5c6483;
        letter-spacing: 0.3px;
    }
    .header-subtitle {
        font-size: 11px;
        font-weight: 600;
        color: #283268;
    }
    .badge-pass,
    .badge-paid  { color:#0d5d39; background:#e4f6ee;
                   padding:3px 9px; border-radius:999px; font-weight:600; }
    .badge-fail,
    .badge-unpaid{ color:#9c1c1c; background:#fde8e8;
                   padding:3px 9px; border-radius:999px; font-weight:600; }
    .badge-part  { color:#7a4f00; background:#fff1da;
                   padding:3px 9px; border-radius:999px; font-weight:600; }
    .status-present { color:#0d5d39; background:#e4f6ee; }
    .status-absent  { color:#9c1c1c; background:#fde8e8; }
    .status-incomplete { color:#7a4f00; background:#fff1da; }
    .status-badge {
        font-weight:600;
        padding:4px 10px;
        border-radius:999px;
    }
    .warning {
        color:#8f3700;
        font-weight:600;
        border:1px solid #f8c6bb;
        border-radius:12px;
        padding:9px 13px;
        background:#fff3ec;
        margin-bottom: 12px;
    }
    .profile-hero {
        display:flex;
        justify-content:space-between;
        align-items:flex-start;
        gap:16px;
        padding:12px 14px;
        border:1px solid #e4e8f5;
        border-radius:14px;
        background:#f9fbff;
        margin-bottom:14px;
    }
    .hero-name {
        font-size:24px;
        font-weight:700;
        color:#0a143d;
        margin:0 0 2px 0;
    }
    .hero-meta {
        font-size:12px;
        color:#5b6384;
    }
    .hero-badges {
        display:flex;
        flex-wrap:wrap;
        gap:6px;
        margin-top:8px;
    }
    .hero-meta-block {
        display:flex;
        gap:16px;
    }
    .hero-stat {
        text-align:right;
    }
    .hero-stat span {
        display:block;
        font-size:10px;
        letter-spacing:1px;
        text-transform:uppercase;
        color:#7d84a6;
    }
    .hero-stat strong {
        font-size:14px;
        color:#0a143d;
    }
    .profile-grid {
        display:grid;
        grid-template-columns:repeat(auto-fit,minmax(330px,1fr));
        gap:16px;
    }
    .profile-col {
        display:flex;
        flex-direction:column;
        gap:14px;
    }
    .profile-card {
        border:1px solid #e0e6f4;
        border-radius:14px;
        padding:12px 14px;
        background:#ffffff;
    }
    .profile-card h4 {
        margin:0 0 6px 0;
        font-size:13px;
        font-weight:700;
        color:#0f172a;
    }
    .pill-row { display:flex; flex-wrap:wrap; gap:6px; }
    .pill {
        padding:5px 10px;
        border-radius:999px;
        background:#eef2ff;
        font-size:11px;
        color:#273383;
        font-weight:600;
    }
    .mini-note {
        font-size:10.2px;
        color:#6a7296;
        margin-top:6px;
    }
    .table-card-empty {
        font-size:11.4px;
        color:#8a91ad;
    }
    .amount-label {
        font-size:11px;
        letter-spacing:1.2px;
        text-transform:uppercase;
        opacity:0.8;
    }
    .amount-value {
        font-size:26px;
        font-weight:700;
        letter-spacing:0.3px;
    }
    .receipt-hero {
        display:flex;
        justify-content:space-between;
        gap:16px;
        padding:14px 16px;
        border:1px solid #e0e6f4;
        border-radius:14px;
        background:#f9fbff;
        margin-bottom:14px;
    }
    .receipt-hero .receipt-id {
        font-size:12px;
        letter-spacing:1px;
        text-transform:uppercase;
        color:#5c6483;
    }
    .receipt-hero .hero-amount {
        text-align:right;
    }
    .receipt-hero .hero-amount .amount-label {
        color:#94a3c7;
    }
    .receipt-grid {
        display:grid;
        grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
        gap:14px;
    }
    .footer {
        margin-top:16px;
        border-top:1px solid #e2e7f2;
        padding-top:8px;
        font-size:10.4px;
        color:#5c6483;
        text-align:center;
    }
"""
# ── Student Profile HTML ──────────────────────────────────────────────────────

def get_student_profile_html(student_id: int) -> str:
    """
    Generate a concise, single-page student profile summary.
    """
    from database.connection import get_session
    from models.student import Student
    from services.subscription_service import (
        get_active_subscription, get_all_payments_for_student,
        get_outstanding_balance,
    )
    from services.attendance_analytics_service import (
        get_monthly_analytics, bs_month_name
    )
    from services.exam_service import get_results_for_student

    session = get_session()
    s = session.query(Student).get(student_id)
    if not s:
        session.close()
        return "<html><body><p>Student not found.</p></body></html>"

    name      = s.name
    uid       = s.user_id
    phone     = s.phone or "—"
    guardian  = s.guardian_name or "—"
    whatsapp  = s.whatsapp_number or "—"
    address   = s.address or "—"
    dob       = bs_str(s.dob)       if s.dob       else "—"
    joined_bs = bs_str(s.join_date) if s.join_date else "—"
    join_date_ad = s.join_date
    cls       = s.class_.name if s.class_ else "—"
    grp       = s.group.name  if s.group  else "—"
    session.close()

    sub         = get_active_subscription(student_id)
    outstanding = get_outstanding_balance(student_id)
    payments    = get_all_payments_for_student(student_id)
    latest_pay  = payments[0] if payments else None
    exam_data   = [
        e for e in get_results_for_student(student_id, join_date_ad)
        if e["has_results"]
    ]
    latest_exam = exam_data[0] if exam_data else None

    if join_date_ad:
        by, bm, _ = ad_to_bs(join_date_ad)
    else:
        by, bm, _ = ad_to_bs(datetime.date.today())
    attendance_stats = get_monthly_analytics(
        student_id, by, bm, join_date_ad
    )

    h = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>{_BASE_CSS}</style>
</head>
<body>
<div class="doc-container">

{_header_html("Student Profile")}
"""

    if outstanding > 0:
        h += f"""
<div class="warning">
  ⚠ Outstanding balance across all subscriptions: Rs. {outstanding:,.0f}
</div>
"""

    hero_badges = []
    if cls and cls != "—":
        hero_badges.append(f"Class {cls}")
    if grp and grp != "—":
        hero_badges.append(f"Group {grp}")

    h += f"""
<div class="profile-hero">
  <div>
    <div class="hero-name">{name}</div>
    <div class="hero-meta">ID #{uid}</div>
    <div class="hero-badges">
      {''.join(f'<span class="pill">{b}</span>' for b in hero_badges) or '<span class="pill">Profile Complete</span>'}
    </div>
  </div>
  <div class="hero-meta-block">
    <div class="hero-stat">
      <span>Joined</span>
      <strong>{joined_bs}</strong>
    </div>
    <div class="hero-stat">
      <span>Date of Birth</span>
      <strong>{dob}</strong>
    </div>
  </div>
</div>
"""

    # Two-column layout
    h += '<div class="profile-grid">'

    # Left column (academics + attendance/exam)
    h += '<div class="profile-col">'

    h += '<div class="profile-card">'
    h += '<h4>Academic Snapshot</h4>'
    h += '<table class="kv-table"><tbody>'
    for k, v in [
        ("Full Name", name),
        ("User ID", uid),
        ("Class", cls),
        ("Group", grp),
    ]:
        h += f'<tr><td class="key">{k}</td><td class="val">{v}</td></tr>'
    h += "</tbody></table></div>"

    h += '<div class="profile-card">'
    h += (
        f"<h4>Attendance · {bs_month_name(attendance_stats['bs_month'])} "
        f"{attendance_stats['bs_year']}</h4>"
    )
    h += "<table><thead><tr><th>Metric</th><th>Days</th></tr></thead><tbody>"
    for label, key in [
        ("Working Days", "working_days"),
        ("Present", "present"),
        ("Incomplete", "incomplete"),
        ("Absent", "absent"),
        ("Holiday", "holiday"),
    ]:
        h += (
            f"<tr><td>{label}</td>"
            f"<td>{attendance_stats.get(key, 0)}</td></tr>"
        )
    h += "</tbody></table></div>"

    if latest_exam:
        h += '<div class="profile-card">'
        h += (
            f"<h4>Latest Exam · {latest_exam['exam']}</h4>"
            f"<p class='hero-meta'>"
            f"{latest_exam['percentage']}% · "
            f"{latest_exam['total_scored']:.0f}/{latest_exam['total_full']:.0f}</p>"
        )
        h += "<table><thead><tr>"
        for col in ["Subject", "Full", "Pass", "Marks", "Result"]:
            h += f"<th>{col}</th>"
        h += "</tr></thead><tbody>"
        for sub_r in latest_exam["subjects"][:3]:
            result = (
                '<span class="badge-pass">Pass</span>'
                if sub_r["passed"] is True else
                '<span class="badge-fail">Fail</span>'
                if sub_r["passed"] is False else "—"
            )
            marks = (
                str(sub_r["marks"]) if sub_r["marks"] is not None else "—"
            )
            h += (
                f"<tr>"
                f"<td>{sub_r['subject']}</td>"
                f"<td>{sub_r['full']}</td>"
                f"<td>{sub_r['pass']}</td>"
                f"<td>{marks}</td>"
                f"<td>{result}</td>"
                f"</tr>"
            )
        if len(latest_exam["subjects"]) > 3:
            h += (
                "<tr><td colspan='5' class='mini-note'>"
                "Additional subjects available inside the app.</td></tr>"
            )
        h += "</tbody></table></div>"
    else:
        h += (
            "<div class='profile-card'><h4>Latest Exam</h4>"
            "<p class='table-card-empty'>No published exam records.</p></div>"
        )

    h += "</div>"  # end left column

    # Right column (contact + subscription + billing)
    h += '<div class="profile-col">'

    h += '<div class="profile-card">'
    h += '<h4>Contact & Guardian</h4>'
    h += '<table class="kv-table"><tbody>'
    for k, v in [
        ("Phone", phone),
        ("WhatsApp", whatsapp),
        ("Guardian", guardian),
        ("Address", address),
    ]:
        h += f'<tr><td class="key">{k}</td><td class="val">{v}</td></tr>'
    h += "</tbody></table></div>"

    h += '<div class="profile-card">'
    h += '<h4>Subscription Status</h4>'
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
            ("Days Covered", sub["days_label"]),
            ("Total Fee", f"Rs. {sub['total_fee']:,.0f}"),
            ("Paid", f"Rs. {sub['total_paid']:,.0f}"),
            ("Balance", f"Rs. {sub['balance']:,.0f}"),
            ("Status", pay_badge),
        ]:
            h += f'<tr><td class="key">{k}</td><td class="val">{v}</td></tr>'
        h += "</tbody></table>"
    else:
        h += "<p class='table-card-empty'>No active subscription.</p>"
    h += "</div>"

    h += '<div class="profile-card">'
    h += '<h4>Billing Overview</h4>'
    h += '<table class="kv-table"><tbody>'
    bal_text = f"Rs. {outstanding:,.0f}" if outstanding > 0 else "Cleared"
    h += (
        f"<tr><td class='key'>Outstanding Balance</td>"
        f"<td class='val'>{bal_text}</td></tr>"
    )
    if latest_pay:
        lp_date = latest_pay["date"]
        lp_str  = bs_str(lp_date) if hasattr(lp_date, "year") else str(lp_date)
        h += (
            f"<tr><td class='key'>Latest Payment</td>"
            f"<td class='val'>{lp_str} · Rs. {latest_pay['amount']:,.0f}</td></tr>"
        )
        h += (
            f"<tr><td class='key'>Method</td>"
            f"<td class='val'>{latest_pay['method']}</td></tr>"
        )
    else:
        h += (
            "<tr><td class='key'>Latest Payment</td>"
            "<td class='val'>No payments recorded</td></tr>"
        )
    h += "</tbody></table></div>"

    h += "</div>"  # end right column
    h += "</div>"  # end profile grid

    h += f"""
<div class="footer">
  Generated: {today_bs()}  ·  {CENTRE_NAME}  ·  {CENTRE_ADDRESS}
</div>
</div>
</body></html>
"""
    return h


def get_teacher_profile_html(teacher_id: int,
                             centre_name: str | None = None,
                             centre_address: str | None = None) -> str:
    """
    Generate a concise teacher profile summary.
    """
    from database.connection import get_session
    from models.teacher import Teacher
    from models.schedule import Schedule
    from models.attendance import TeacherAttendance
    from services.attendance_analytics_service import (
        get_teacher_two_month_analytics, bs_month_name
    )

    session = get_session()
    t = session.query(Teacher).get(teacher_id)
    if not t:
        session.close()
        return "<html><body><p>Teacher not found.</p></body></html>"

    join_bs = bs_str(t.join_date) if t.join_date else "—"
    phone   = t.phone or "—"
    subject = t.subject or "—"
    address = t.address or "—"

    att_records = session.query(TeacherAttendance).filter(
        TeacherAttendance.teacher_id == teacher_id
    ).order_by(TeacherAttendance.date.desc()).limit(8).all()

    schedules = session.query(Schedule).filter_by(
        teacher_id=teacher_id
    ).order_by(Schedule.day_of_week.asc(), Schedule.start_time.asc()).all()
    session.close()

    analytics = get_teacher_two_month_analytics(teacher_id, t.join_date)
    centre_name = centre_name or CENTRE_NAME
    centre_address = centre_address or CENTRE_ADDRESS

    def _month_label(stats: dict | None) -> str:
        if not stats or not stats.get("bs_month"):
            return "—"
        return f"{bs_month_name(stats['bs_month'])} {stats.get('bs_year', '')}".strip()

    primary_att = (
        analytics.get("current") if analytics.get("current", {}).get("bs_month")
        else analytics.get("previous")
    ) or {}

    month_rows = []
    for key in ("current", "previous"):
        stats = analytics.get(key)
        if not stats or not stats.get("bs_month"):
            continue
        label = f"{bs_month_name(stats['bs_month'])} {stats.get('bs_year', '')}".strip()
        month_rows.append(
            f"<tr><td>{label}</td>"
            f"<td>{stats.get('present', 0)}</td>"
            f"<td>{stats.get('absent', 0)}</td>"
            f"<td>{stats.get('incomplete', 0)}</td>"
            f"<td>{stats.get('holiday', 0)}</td></tr>"
        )

    h = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>{_BASE_CSS}</style>
</head>
<body>
<div class="doc-container">

{_header_html("Teacher Profile", centre_name, centre_address)}

<div class="profile-hero">
  <div>
    <div class="hero-name">{t.name}</div>
    <div class="hero-meta">Teacher ID #{t.user_id}</div>
    <div class="hero-badges">
      <span class="pill">Subject · {subject}</span>
    </div>
  </div>
  <div class="hero-meta-block">
    <div class="hero-stat">
      <span>Joined</span>
      <strong>{join_bs}</strong>
    </div>
    <div class="hero-stat">
      <span>Contact</span>
      <strong>{phone}</strong>
    </div>
  </div>
</div>

<div class="profile-grid">
  <div class="profile-col">
    <div class="profile-card">
      <h4>Professional Snapshot</h4>
      <table class="kv-table"><tbody>
        <tr><td class="key">Name</td><td class="val">{t.name}</td></tr>
        <tr><td class="key">Teacher ID</td><td class="val">{t.user_id}</td></tr>
        <tr><td class="key">Primary Subject</td><td class="val">{subject}</td></tr>
        <tr><td class="key">Join Date (BS)</td><td class="val">{join_bs}</td></tr>
      </tbody></table>
    </div>

    <div class="profile-card">
      <h4>Attendance Overview · {_month_label(primary_att)}</h4>
      <table><thead><tr><th>Metric</th><th>Days</th></tr></thead><tbody>
        <tr><td>Working Days</td><td>{primary_att.get('working_days', 0)}</td></tr>
        <tr><td>Present Days</td><td>{primary_att.get('present', 0)}</td></tr>
        <tr><td>Incomplete</td><td>{primary_att.get('incomplete', 0)}</td></tr>
        <tr><td>Absent Days</td><td>{primary_att.get('absent', 0)}</td></tr>
        <tr><td>Holiday</td><td>{primary_att.get('holiday', 0)}</td></tr>
      </tbody></table>
"""
    if month_rows:
        h += (
            "<p style='font-size:11px;color:#555555;margin:6px 0 4px 0;'>"
            "Last two BS months</p>"
            "<table><thead><tr><th>Month</th><th>Present</th><th>Absent</th>"
            "<th>Incomplete</th><th>Holiday</th></tr></thead><tbody>"
            f"{''.join(month_rows)}</tbody></table>"
        )

    h += """
    </div>

    <div class="profile-card">
      <h4>Recent Attendance</h4>
"""
    if att_records:
        h += "<table><thead><tr><th>Date (BS)</th><th>Entry</th><th>Exit</th><th>Status</th></tr></thead><tbody>"
        for rec in att_records:
            entry = rec.entry_time or "—"
            exit_t = rec.exit_time or "—"
            h += (
                f"<tr><td>{bs_str(rec.date)}</td>"
                f"<td>{entry}</td>"
                f"<td>{exit_t}</td>"
                f"<td>{_status_badge_html(rec.status or 'Absent')}</td></tr>"
            )
        h += "</tbody></table>"
    else:
        h += "<p class='table-card-empty'>No attendance records yet.</p>"
    h += "</div></div>"

    h += '<div class="profile-col">'
    h += """
    <div class="profile-card">
      <h4>Contact & Address</h4>
      <table class="kv-table"><tbody>
        <tr><td class="key">Phone</td><td class="val">{phone}</td></tr>
        <tr><td class="key">Address</td><td class="val">{address}</td></tr>
      </tbody></table>
    </div>
""".format(phone=phone, address=address)

    h += '<div class="profile-card">'
    h += '<h4>Assigned Schedule</h4>'
    if schedules:
        h += "<table><thead><tr><th>Day</th><th>Class</th><th>Group</th><th>Subject</th><th>Time</th></tr></thead><tbody>"
        for sch in schedules:
            class_name = sch.class_.name if sch.class_ else "—"
            group_name = sch.group.name if sch.group else "—"
            subj = sch.subject or "—"
            start = sch.start_time.strftime("%H:%M") if sch.start_time else "—"
            end = sch.end_time.strftime("%H:%M") if sch.end_time else "—"
            h += (
                f"<tr><td>{sch.day_of_week}</td>"
                f"<td>{class_name}</td>"
                f"<td>{group_name}</td>"
                f"<td>{subj}</td>"
                f"<td>{start} - {end}</td></tr>"
            )
        h += "</tbody></table>"
    else:
        h += "<p class='table-card-empty'>No schedule assigned.</p>"
    h += "</div>"

    h += "</div></div>"  # end profile grid

    h += f"""
<div class="footer">
  Generated: {today_bs()}  ·  {centre_name}  ·  {centre_address}
</div>
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

    # Attendance + exam context (two recent BS months + last exam snapshot)
    attendance_rows = ""
    last_exam_summary = "No published exam records."
    if s:
        from services.attendance_analytics_service import (
            get_two_month_analytics, bs_month_name
        )
        from services.exam_service import get_results_for_student

        analytics = get_two_month_analytics(s.id, s.join_date)
        rows_html = []
        for key, label in (("current", "Current Month"),
                           ("previous", "Previous Month")):
            stats = analytics.get(key) if analytics else None
            if not stats or not stats.get("bs_month"):
                continue
            month_label = f"{bs_month_name(stats['bs_month'])} {stats.get('bs_year', '')}".strip()
            rows_html.append(
                f"<tr><td>{month_label}</td>"
                f"<td>{stats.get('working_days', 0)}</td>"
                f"<td>{stats.get('present', 0)}</td>"
                f"<td>{stats.get('absent', 0)}</td></tr>"
            )
        if rows_html:
            attendance_rows = (
                "<div style='margin-top:10px;'>"
                "<strong style='font-size:11px;color:#555555;'>Attendance · Last 2 Months</strong>"
                "<table style='margin-top:4px;'><thead>"
                "<tr><th>Month</th><th>Working</th><th>Present</th><th>Absent</th></tr></thead><tbody>"
                f"{''.join(rows_html)}"
                "</tbody></table></div>"
            )

        exam_data = [
            e for e in get_results_for_student(s.id, s.join_date)
            if e["has_results"]
        ]
        if exam_data:
            latest_exam = exam_data[0]
            subject_bits = []
            for subj in latest_exam["subjects"]:
                marks = "—" if subj["marks"] is None else str(subj["marks"])
                subject_bits.append(f"{subj['subject']}: {marks}")
                if len(subject_bits) >= 3:
                    break
            if len(latest_exam["subjects"]) > 3:
                subject_bits.append("...")
            last_exam_summary = (
                f"{latest_exam['exam']} — " + ", ".join(subject_bits)
            )

    method     = p.payment_method or "—"
    amount_str = f"Rs. {p.amount_paid:,.0f}"
    note_text  = p.note or "—"
    receipt_id = p.id if p.id is not None else "—"

    h = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>{_BASE_CSS}</style>
</head>
<body>
<div class="doc-container compact">

{_header_html("Payment Receipt")}

<div class="receipt-hero">
  <div>
    <div class="receipt-id">Receipt #{receipt_id}</div>
    <div class="hero-meta">Issued {pdate}</div>
    <div class="pill-row" style="margin-top:8px;">
      <span class="pill">Method · {method}</span>
      <span class="pill">Recorded · {created}</span>
    </div>
  </div>
  <div class="hero-amount">
    <div class="amount-label">Amount Paid</div>
    <div class="amount-value">{amount_str}</div>
  </div>
</div>

<div class="receipt-grid">
  <div class="profile-card">
    <h4>Student</h4>
    <table class="kv-table"><tbody>
      <tr><td class="key">Name</td>
          <td class="val"><strong>{s.name if s else '—'}</strong></td></tr>
      <tr><td class="key">User ID</td>
          <td class="val">{s.user_id if s else '—'}</td></tr>
      <tr><td class="key">Phone</td>
          <td class="val">{s.phone or '—' if s else '—'}</td></tr>
      <tr><td class="key">Last Exam Result</td>
          <td class="val">{last_exam_summary}</td></tr>
    </tbody></table>
    {attendance_rows}
  </div>

  <div class="profile-card">
    <h4>Subscription</h4>
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

    h += """
    </tbody></table>
  </div>
</div>

<div class="profile-card">
  <h4>Payment Details</h4>
  <table class="kv-table"><tbody>
    <tr><td class="key">Amount Paid</td>
        <td class="val">{amount_str}</td></tr>
    <tr><td class="key">Receipt ID</td>
        <td class="val">{receipt_id}</td></tr>
    <tr><td class="key">Method</td>
        <td class="val">{method}</td></tr>
    <tr><td class="key">Notes</td>
        <td class="val">{note_text}</td></tr>
  </tbody></table>
</div>
"""

    if bal > 0:
        h += f"""
<p class="mini-note">Remaining balance for this subscription: Rs. {bal:,.0f}</p>
"""

    h += f"""
<div class="footer">
  Generated: {created}  ·  Computer generated receipt.<br/>
  {CENTRE_NAME}  ·  {CENTRE_ADDRESS}
</div>
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

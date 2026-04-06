"""
PDF export utilities:
- Export student list
- Export individual student profile
"""
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from database.connection import get_session
from models.student import Student
from utils.bs_converter import bs_str
from datetime import date
import logging

logger = logging.getLogger(__name__)

styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "title",
    parent=styles["Heading1"],
    fontSize=16,
    spaceAfter=6,
    textColor=colors.HexColor("#1a1a1a"),
)
SUBTITLE_STYLE = ParagraphStyle(
    "subtitle",
    parent=styles["Normal"],
    fontSize=10,
    textColor=colors.HexColor("#666666"),
    spaceAfter=12,
)
SECTION_STYLE = ParagraphStyle(
    "section",
    parent=styles["Heading2"],
    fontSize=12,
    spaceBefore=12,
    spaceAfter=6,
    textColor=colors.HexColor("#1a1a1a"),
)
BODY_STYLE = ParagraphStyle(
    "body",
    parent=styles["Normal"],
    fontSize=10,
    textColor=colors.HexColor("#1a1a1a"),
    spaceAfter=4,
)

TABLE_HEADER_STYLE = TableStyle([
    ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#2c2c2c")),
    ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
    ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE",    (0, 0), (-1, 0), 10),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
     [colors.HexColor("#ffffff"), colors.HexColor("#f7f7f7")]),
    ("FONTSIZE",    (0, 1), (-1, -1), 9),
    ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
    ("TEXTCOLOR",   (0, 1), (-1, -1), colors.HexColor("#1a1a1a")),
    ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#e0e0e0")),
    ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ("PADDING",     (0, 0), (-1, -1), 6),
    ("TOPPADDING",  (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
])


# ── Export student list ───────────────────────────────────────────────────────

def export_student_list_pdf(filepath: str,
                             centre_name: str = "Tuition Centre"):
    session = get_session()
    students = session.query(Student).order_by(Student.name).all()

    rows = [["#", "User ID", "Name", "Phone", "Class", "Group", "Join Date (BS)"]]
    for i, s in enumerate(students, 1):
        rows.append([
            str(i),
            s.user_id,
            s.name,
            s.phone or "—",
            s.class_.name if s.class_ else "—",
            s.group.name  if s.group  else "—",
            bs_str(s.join_date) if s.join_date else "—",
        ])
    session.close()

    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    content = []
    content.append(Paragraph(centre_name, TITLE_STYLE))
    content.append(Paragraph(
        f"Student List  ·  Generated: {bs_str(date.today())}  "
        f"·  Total: {len(students)} students",
        SUBTITLE_STYLE
    ))
    content.append(HRFlowable(width="100%", thickness=1,
                               color=colors.HexColor("#2c2c2c")))
    content.append(Spacer(1, 10))

    col_widths = [1*cm, 2*cm, 5*cm, 3*cm, 3*cm, 3*cm, 3*cm]
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TABLE_HEADER_STYLE)
    content.append(t)

    doc.build(content)
    logger.info(f"Student list PDF exported: {filepath}")


# ── Export student profile ────────────────────────────────────────────────────

def export_student_profile_pdf(student_id: int, filepath: str,
                                centre_name: str = "Tuition Centre"):
    from services.subscription_service import (
        get_active_subscription, get_subscription_history
    )
    from services.attendance_analytics_service import get_two_month_analytics
    from services.exam_service import get_results_for_student

    session = get_session()
    s = session.query(Student).get(student_id)
    if not s:
        session.close()
        return

    name    = s.name
    uid     = s.user_id
    phone   = s.phone or "—"
    address = s.address or "—"
    dob     = bs_str(s.dob)      if s.dob      else "—"
    joined  = bs_str(s.join_date) if s.join_date else "—"
    cls     = s.class_.name if s.class_ else "—"
    grp     = s.group.name  if s.group  else "—"

    atts = sorted(s.attendances, key=lambda a: a.date, reverse=True)
    session.close()

    sub        = get_active_subscription(student_id)
    analytics  = get_two_month_analytics(student_id)
    exam_data  = get_results_for_student(student_id)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    content = []

    # Header
    content.append(Paragraph(centre_name, TITLE_STYLE))
    content.append(Paragraph("Student Profile", SECTION_STYLE))
    content.append(HRFlowable(width="100%", thickness=1,
                               color=colors.HexColor("#2c2c2c")))
    content.append(Spacer(1, 8))

    # Personal details table
    info_data = [
        ["Name",           name,    "User ID",    uid],
        ["Phone",          phone,   "Class",      cls],
        ["Address",        address, "Group",      grp],
        ["Date of Birth",  dob,     "Join Date",  joined],
    ]
    info_t = Table(info_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 6*cm])
    info_t.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",  (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1a1a1a")),
        ("GRID",      (0, 0), (-1, -1), 0.3, colors.HexColor("#e0e0e0")),
        ("PADDING",   (0, 0), (-1, -1), 6),
        ("BACKGROUND",(0, 0), (0, -1), colors.HexColor("#f5f5f5")),
        ("BACKGROUND",(2, 0), (2, -1), colors.HexColor("#f5f5f5")),
    ]))
    content.append(info_t)
    content.append(Spacer(1, 12))

    # Subscription
    content.append(Paragraph("Active Subscription", SECTION_STYLE))
    if sub:
        sub_data = [
            ["Period (BS)",  f"{bs_str(sub['start_date'])} → {bs_str(sub['end_date'])}",
             "Days Left",   f"{sub['days_left']} days"],
            ["Total Fee",   f"Rs. {sub['total_fee']:,.0f}",
             "Paid",        f"Rs. {sub['total_paid']:,.0f}"],
            ["Balance",     f"Rs. {sub['balance']:,.0f}",
             "Status",      sub["pay_status"].capitalize()],
        ]
    else:
        sub_data = [["No active subscription", "", "", ""]]

    sub_t = Table(sub_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 6*cm])
    sub_t.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",  (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1a1a1a")),
        ("GRID",      (0, 0), (-1, -1), 0.3, colors.HexColor("#e0e0e0")),
        ("PADDING",   (0, 0), (-1, -1), 6),
        ("BACKGROUND",(0, 0), (0, -1), colors.HexColor("#f5f5f5")),
        ("BACKGROUND",(2, 0), (2, -1), colors.HexColor("#f5f5f5")),
    ]))
    content.append(sub_t)
    content.append(Spacer(1, 12))

    # Attendance analytics
    content.append(Paragraph("Monthly Attendance Summary", SECTION_STYLE))
    cur  = analytics["current"]
    prev = analytics["previous"]
    from calendar import month_name

    att_data = [
        ["Period", "Working Days", "Present", "Absent", "Incomplete", "Holiday"],
        [
            f"{month_name[cur['month']]} {cur['year']}",
            str(cur["working_days"]),
            str(cur["present"]),
            str(cur["absent"]),
            str(cur["incomplete"]),
            str(cur["holiday"]),
        ],
        [
            f"{month_name[prev['month']]} {prev['year']}",
            str(prev["working_days"]),
            str(prev["present"]),
            str(prev["absent"]),
            str(prev["incomplete"]),
            str(prev["holiday"]),
        ],
    ]
    att_t = Table(att_data, colWidths=[4*cm, 3*cm, 2.5*cm, 2.5*cm, 3*cm, 2.5*cm])
    att_t.setStyle(TABLE_HEADER_STYLE)
    content.append(att_t)
    content.append(Spacer(1, 12))

    # Exam results
    if exam_data:
        content.append(Paragraph("Examination Results", SECTION_STYLE))
        for exam in exam_data:
            content.append(Paragraph(exam["exam"], BODY_STYLE))
            ex_rows = [["Subject", "Full Marks", "Pass Marks",
                        "Obtained", "Result"]]
            for sub_r in exam["subjects"]:
                result_str = (
                    "Pass" if sub_r["passed"] is True  else
                    "Fail" if sub_r["passed"] is False else
                    "—"
                )
                ex_rows.append([
                    sub_r["subject"],
                    str(sub_r["full"]),
                    str(sub_r["pass"]),
                    str(sub_r["marks"]) if sub_r["marks"] is not None else "—",
                    result_str,
                ])
            if exam["has_results"]:
                ex_rows.append([
                    "TOTAL",
                    str(exam["total_full"]),
                    "—",
                    str(exam["total_scored"]),
                    f"{exam['percentage']}%",
                ])
            ex_t = Table(ex_rows,
                         colWidths=[5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
            ex_t.setStyle(TABLE_HEADER_STYLE)
            content.append(ex_t)
            content.append(Spacer(1, 8))

    # Recent attendance (last 20)
    content.append(Paragraph("Recent Attendance (Last 20 Days)", SECTION_STYLE))
    rec_rows = [["Date (BS)", "Entry", "Exit", "Status"]]
    for att in atts[:20]:
        rec_rows.append([
            bs_str(att.date),
            str(att.entry_time) if att.entry_time else "—",
            str(att.exit_time)  if att.exit_time  else "—",
            att.status or "—",
        ])
    rec_t = Table(rec_rows, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    rec_t.setStyle(TABLE_HEADER_STYLE)
    content.append(rec_t)

    # Footer
    content.append(Spacer(1, 16))
    content.append(HRFlowable(width="100%", thickness=0.5,
                               color=colors.HexColor("#cccccc")))
    content.append(Paragraph(
        f"Generated: {bs_str(date.today())}  ·  {centre_name}",
        ParagraphStyle("footer", parent=styles["Normal"],
                       fontSize=8, textColor=colors.HexColor("#888888"))
    ))

    doc.build(content)
    logger.info(f"Student profile PDF exported: {filepath}")
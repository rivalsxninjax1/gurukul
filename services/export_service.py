"""
PDF export utilities — student list + student profile (refined).
Profile PDF:
  - No raw attendance log (removed)
  - Only exams within the last BS month and after join date
  - Clean layout
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
from utils.bs_converter import bs_str, today_bs_tuple, bs_month_ad_range, ad_to_bs
from datetime import date
import logging

CENTRE_NAME    = "GURUKUL ACADEMY AND TRAINING CENTER"
CENTRE_ADDRESS = "Biratnagar-1, Bhatta Chowk"


logger = logging.getLogger(__name__)

styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "title", parent=styles["Heading1"], fontSize=16,
    spaceAfter=6, textColor=colors.HexColor("#1a1a1a"),
)
SUBTITLE_STYLE = ParagraphStyle(
    "subtitle", parent=styles["Normal"], fontSize=10,
    textColor=colors.HexColor("#666666"), spaceAfter=12,
)
SECTION_STYLE = ParagraphStyle(
    "section", parent=styles["Heading2"], fontSize=12,
    spaceBefore=12, spaceAfter=6,
    textColor=colors.HexColor("#1a1a1a"),
)
BODY_STYLE = ParagraphStyle(
    "body", parent=styles["Normal"], fontSize=10,
    textColor=colors.HexColor("#1a1a1a"), spaceAfter=4,
)

TBL_STYLE = TableStyle([
    ("BACKGROUND",     (0, 0), (-1, 0), colors.HexColor("#2c2c2c")),
    ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
    ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE",       (0, 0), (-1, 0), 10),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
     [colors.HexColor("#ffffff"), colors.HexColor("#f7f7f7")]),
    ("FONTSIZE",       (0, 1), (-1, -1), 9),
    ("FONTNAME",       (0, 1), (-1, -1), "Helvetica"),
    ("TEXTCOLOR",      (0, 1), (-1, -1), colors.HexColor("#1a1a1a")),
    ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#e0e0e0")),
    ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING",     (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING",  (0, 0), (-1, -1), 7),
    ("LEFTPADDING",    (0, 0), (-1, -1), 6),
    ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
])

INFO_STYLE = TableStyle([
    ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
    ("FONTNAME",   (2, 0), (2, -1), "Helvetica-Bold"),
    ("FONTSIZE",   (0, 0), (-1, -1), 9),
    ("TEXTCOLOR",  (0, 0), (-1, -1), colors.HexColor("#1a1a1a")),
    ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#e0e0e0")),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f5f5f5")),
])

def _build_pdf_header(content: list, centre_name: str,
                       subtitle: str):
    """
    Build standard PDF header with logo (if available) + institution name + address.
    Appends flowables to `content` list.
    """
    from reportlab.platypus import HRFlowable, Spacer, Image as RLImage
    from reportlab.lib import colors
    from utils.logo_helper import get_logo_path
    import os

    logo_path = get_logo_path()
    if os.path.isfile(logo_path):
        try:
            from PIL import Image as PILImage
            with PILImage.open(logo_path) as img:
                iw, ih = img.size
            max_h = 50
            ratio  = max_h / ih
            rl_img = RLImage(logo_path,
                             width  = iw * ratio,
                             height = ih * ratio)
            rl_img.hAlign = "CENTER"
            content.append(rl_img)
            content.append(Spacer(1, 6))
        except Exception:
            pass

    content.append(Paragraph(centre_name, TITLE_STYLE))
    content.append(Paragraph(
        CENTRE_ADDRESS, SUBTITLE_STYLE
    ))
    content.append(Paragraph(subtitle, SUBTITLE_STYLE))
    content.append(HRFlowable(
        width="100%", thickness=1, color=colors.HexColor("#2c2c2c")
    ))
    content.append(Spacer(1, 10))


def export_student_list_pdf(filepath: str,
                             centre_name: str = "GURUKUL ACADEMY AND TRAINING CENTER"):
    session = get_session()
    students = session.query(Student).order_by(Student.name).all()
    rows = [["#", "User ID", "Name", "Phone",
             "Guardian", "Class", "Group", "Join Date (BS)"]]
    for i, s in enumerate(students, 1):
        rows.append([
            str(i),
            s.user_id,
            s.name,
            s.phone or "—",
            s.guardian_name or "—",
            s.class_.name if s.class_ else "—",
            s.group.name  if s.group  else "—",
            bs_str(s.join_date) if s.join_date else "—",
        ])
    session.close()

    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm,  bottomMargin=1.5*cm
    )
    content = []
    _build_pdf_header(
        content, CENTRE_NAME,
        f"Student List  ·  Generated: {bs_str(date.today())}"
        f"  ·  Total: {len(students)} students"
    )

    col_w = [0.8*cm, 1.8*cm, 4.5*cm, 2.5*cm,
             3*cm, 2.5*cm, 2.5*cm, 2.8*cm]
    t = Table(rows, colWidths=col_w, repeatRows=1)
    t.setStyle(TBL_STYLE)
    content.append(t)
    doc.build(content)
    logger.info(f"Student list PDF: {filepath}")


def export_student_profile_pdf(student_id: int, filepath: str,
                                centre_name: str = "GURUKUL ACADEMY AND TRAINING CENTER"):
    from services.subscription_service import (
        get_active_subscription, get_subscription_history
    )
    from services.attendance_analytics_service import (
        get_two_month_analytics, bs_month_name
    )
    from services.exam_service import get_results_for_student

    session = get_session()
    s = session.query(Student).get(student_id)
    if not s:
        session.close()
        return

    name      = s.name
    uid       = s.user_id
    phone     = s.phone or "—"
    guardian  = s.guardian_name or "—"
    whatsapp  = s.whatsapp_number or "—"
    address   = s.address or "—"
    dob       = bs_str(s.dob)       if s.dob       else "—"
    joined    = bs_str(s.join_date) if s.join_date else "—"
    join_date_ad = s.join_date
    cls       = s.class_.name if s.class_ else "—"
    grp       = s.group.name  if s.group  else "—"
    session.close()

    sub       = get_active_subscription(student_id)
    analytics = get_two_month_analytics(student_id, join_date_ad)
    all_exams = get_results_for_student(student_id)

    # Filter exams: only those after join date and within last 1 BS month
    today_bs_y, today_bs_m, _ = today_bs_tuple()
    cur_start, cur_end = bs_month_ad_range(today_bs_y, today_bs_m)
    # Include current and previous BS month
    from utils.bs_converter import prev_bs_month as _prev
    prev_y, prev_m = _prev(today_bs_y, today_bs_m)
    prev_start, _ = bs_month_ad_range(prev_y, prev_m)
    exam_cutoff = prev_start  # show exams from previous BS month onward

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm,  bottomMargin=1.5*cm
    )
    content = []

    # Header
    _build_pdf_header(content, CENTRE_NAME, "Student Profile")

    # Personal details
    info_data = [
        ["Name",      name,     "User ID",   uid],
        ["Phone",     phone,    "WhatsApp",  whatsapp],
        ["Guardian",  guardian, "Class",     cls],
        ["Address",   address,  "Group",     grp],
        ["DOB (BS)",  dob,      "Join (BS)", joined],
    ]
    info_t = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
    info_t.setStyle(INFO_STYLE)
    content.append(info_t)
    content.append(Spacer(1, 12))

    # Active subscription
    content.append(Paragraph("Active Subscription", SECTION_STYLE))
    if sub:
        sub_data = [
            ["Period (BS)", f"{bs_str(sub['start_date'])} → {bs_str(sub['end_date'])}",
             "Days Left",   f"{sub['days_left']} days"],
            ["Total Fee",   f"Rs. {sub['total_fee']:,.0f}",
             "Paid",        f"Rs. {sub['total_paid']:,.0f}"],
            ["Balance",     f"Rs. {sub['balance']:,.0f}",
             "Status",      sub["pay_status"].capitalize()],
        ]
    else:
        sub_data = [["No active subscription", "", "", ""]]
    sub_t = Table(sub_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
    sub_t.setStyle(INFO_STYLE)
    content.append(sub_t)
    content.append(Spacer(1, 12))

    # Attendance summary (BS months only — no raw log)
    content.append(Paragraph("Attendance Summary", SECTION_STYLE))
    cur  = analytics["current"]
    prev = analytics["previous"]
    att_data = [
        ["BS Month", "Working Days", "Present",
         "Absent", "Incomplete", "Holiday"],
        [
            f"{bs_month_name(cur['bs_month'])} {cur['bs_year']}",
            str(cur["working_days"]), str(cur["present"]),
            str(cur["absent"]), str(cur["incomplete"]), str(cur["holiday"]),
        ],
        [
            f"{bs_month_name(prev['bs_month'])} {prev['bs_year']}",
            str(prev["working_days"]), str(prev["present"]),
            str(prev["absent"]), str(prev["incomplete"]), str(prev["holiday"]),
        ],
    ]
    att_t = Table(att_data,
                  colWidths=[4*cm, 3*cm, 2.5*cm, 2.5*cm, 3*cm, 2.5*cm])
    att_t.setStyle(TBL_STYLE)
    content.append(att_t)
    content.append(Spacer(1, 12))

    # Exam results — only recent exams (last 1 BS month + after join date)
    recent_exams = [e for e in all_exams if e["has_results"]]
    # We filter by "has results" only — exam dates not tracked per-record
    # so we include all exams that have marks entered
    if recent_exams:
        content.append(Paragraph("Examination Results", SECTION_STYLE))
        for exam in recent_exams:
            content.append(Paragraph(exam["exam"], BODY_STYLE))
            ex_rows = [["Subject", "Full", "Pass", "Obtained", "Result"]]
            for sub_r in exam["subjects"]:
                ex_rows.append([
                    sub_r["subject"],
                    str(sub_r["full"]),
                    str(sub_r["pass"]),
                    str(sub_r["marks"]) if sub_r["marks"] is not None else "—",
                    ("Pass" if sub_r["passed"] is True  else
                     "Fail" if sub_r["passed"] is False else "—"),
                ])
            if exam["has_results"]:
                ex_rows.append([
                    "TOTAL", str(exam["total_full"]), "—",
                    str(exam["total_scored"]),
                    f"{exam['percentage']}%",
                ])
            ex_t = Table(ex_rows,
                         colWidths=[5*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm])
            ex_t.setStyle(TBL_STYLE)
            content.append(ex_t)
            content.append(Spacer(1, 8))

    # Footer
    content.append(Spacer(1, 16))
    content.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#cccccc")
    ))
    content.append(Paragraph(
        f"Generated: {bs_str(date.today())}  ·  {centre_name}",
        ParagraphStyle("footer", parent=styles["Normal"],
                       fontSize=8, textColor=colors.HexColor("#888888"))
    ))
    doc.build(content)
    logger.info(f"Student profile PDF: {filepath}")
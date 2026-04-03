from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def generate_bill_pdf(billing_obj, output_path: str):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Header
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 60, "Tuition Centre")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, "Fee Receipt")

    # Divider
    c.line(50, height - 95, width - 50, height - 95)

    # Bill details
    c.setFont("Helvetica", 12)
    y = height - 130
    details = [
        ("Bill ID",     str(billing_obj.id)),
        ("Student",     billing_obj.student.name if billing_obj.student else "N/A"),
        ("Student ID",  billing_obj.student.user_id if billing_obj.student else "N/A"),
        ("Amount",      f"Rs. {billing_obj.amount:.2f}"),
        ("Due Date",    str(billing_obj.due_date) if billing_obj.due_date else "N/A"),
        ("Status",      billing_obj.paid),
        ("Note",        billing_obj.note or ""),
    ]
    for label, value in details:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(60, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(180, y, value)
        y -= 28

    # Footer
    c.line(50, 80, width - 50, 80)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.grey)
    c.drawString(50, 65, "This is a computer-generated receipt.")

    c.save()
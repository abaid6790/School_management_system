import io

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable

from app.services.salary_service import compute_net_salary


def build_salary_slip_pdf(record) -> bytes:
    school = record.school
    net_salary = compute_net_salary(record)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
                            leftMargin=18 * mm, rightMargin=18 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=16, spaceAfter=2)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
    heading_style = ParagraphStyle("HeadingCustom", parent=styles["Heading3"], spaceBefore=10, spaceAfter=4)

    elements = [Paragraph(school.name, title_style)]
    contact_bits = [b for b in [school.address, school.phone, school.email] if b]
    if contact_bits:
        elements.append(Paragraph(" | ".join(contact_bits), subtitle_style))
    elements.append(Spacer(1, 4 * mm))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#333333")))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph("Salary Slip", heading_style))

    info_data = [
        ["Employee Name:", record.recipient_name, "Employee Type:", record.recipient_role.value.title()],
        ["Month:", record.month.strftime("%B %Y"), "Payment Status:", record.payment_status.value.title()],
    ]
    if record.payment_status.value == "paid":
        info_data.append(["Payment Date:", str(record.payment_date), "", ""])

    info_table = Table(info_data, colWidths=[30 * mm, 60 * mm, 30 * mm, 50 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))

    breakdown_data = [
        ["Basic Salary", str(record.basic_salary)],
        ["Allowances", str(record.allowances)],
        ["Bonus", str(record.bonus)],
        ["Deductions", f"-{record.deductions}"],
        ["Net Salary", str(net_salary)],
    ]
    breakdown_table = Table(breakdown_data, colWidths=[60 * mm, 50 * mm])
    breakdown_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 0.75, colors.HexColor("#333333")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(breakdown_table)
    elements.append(Spacer(1, 8 * mm))
    if record.notes:
        elements.append(Paragraph(f"Notes: {record.notes}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

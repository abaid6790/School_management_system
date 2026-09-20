import io
from datetime import date as date_cls

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable

from app.services.fee_service import compute_fee_totals


def build_fee_statement_pdf(student, fee_rows) -> bytes:
    """fee_rows: list of {"fee": StudentFee, "totals": dict} — same shape the
    student fee page already uses, so the PDF and the on-screen view can never
    show different numbers for the same student."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=16, spaceAfter=2)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
    heading_style = ParagraphStyle("HeadingCustom", parent=styles["Heading3"], spaceBefore=10, spaceAfter=4)

    school = student.school
    elements = [Paragraph(school.name, title_style)]
    contact_bits = [b for b in [school.address, school.phone, school.email] if b]
    if contact_bits:
        elements.append(Paragraph(" | ".join(contact_bits), subtitle_style))
    elements.append(Spacer(1, 4 * mm))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#333333")))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph("Fee Statement", heading_style))

    class_label = f"{student.current_class.name} - {student.current_section.name}" if student.current_class else "-"
    info_data = [["Student Name:", student.name, "Admission No.:", student.admission_number],
                 ["Class:", class_label, "Statement Date:", str(date_cls.today())]]
    info_table = Table(info_data, colWidths=[28 * mm, 62 * mm, 28 * mm, 52 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))

    table_data = [["Fee Type", "Due Date", "Amount", "Discount", "Paid", "Remaining", "Status"]]
    total_amount = total_discount = total_paid = total_remaining = 0
    for row in fee_rows:
        fee, totals = row["fee"], row["totals"]
        table_data.append([
            fee.fee_type.name, str(fee.due_date), str(totals["amount"]), str(totals["discount_total"]),
            str(totals["paid_total"]), str(totals["remaining"]), totals["status"].value.replace("_", " ").title(),
        ])
        total_amount += totals["amount"]
        total_discount += totals["discount_total"]
        total_paid += totals["paid_total"]
        total_remaining += totals["remaining"]
    table_data.append(["TOTAL", "", str(total_amount), str(total_discount), str(total_paid), str(total_remaining), ""])

    fee_table = Table(table_data, colWidths=[35 * mm, 22 * mm, 20 * mm, 20 * mm, 20 * mm, 22 * mm, 25 * mm])
    fee_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f3f5")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(fee_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def build_receipt_pdf(payment) -> bytes:
    student_fee = payment.student_fee
    student = student_fee.student
    school = student_fee.school
    totals = compute_fee_totals(student_fee)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
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
    elements.append(Paragraph("Fee Payment Receipt", heading_style))

    class_label = f"{student.current_class.name} - {student.current_section.name}" if student.current_class else "-"
    info_data = [
        ["Receipt No.:", payment.receipt_number, "Date:", str(payment.payment_date)],
        ["Student Name:", student.name, "Admission No.:", student.admission_number],
        ["Class:", class_label, "Fee Type:", student_fee.fee_type.name],
    ]
    info_table = Table(info_data, colWidths=[28 * mm, 62 * mm, 28 * mm, 52 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))

    summary_data = [
        ["Fee Amount:", f"{student_fee.amount}"],
        ["Discount:", f"{totals['discount_total']}"],
        ["Net Payable:", f"{totals['net_amount']}"],
        ["This Payment:", f"{payment.amount}"],
        ["Payment Method:", payment.payment_method.value.replace("_", " ").title()],
        ["Total Paid So Far:", f"{totals['paid_total']}"],
        ["Remaining Balance:", f"{totals['remaining']}"],
    ]
    summary_table = Table(summary_data, colWidths=[45 * mm, 55 * mm])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (0, 3), (1, 3), "Helvetica-Bold"),  # emphasize "This Payment" row
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LINEABOVE", (0, 3), (-1, 3), 0.5, colors.HexColor("#cccccc")),
        ("LINEBELOW", (0, 3), (-1, 3), 0.5, colors.HexColor("#cccccc")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 10 * mm))

    if payment.notes:
        elements.append(Paragraph(f"Notes: {payment.notes}", styles["Normal"]))
        elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph(
        f"Received by: {payment.received_by.name if payment.received_by else '-'}", styles["Normal"]
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

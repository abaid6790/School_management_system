"""
Built with ReportLab's layout primitives directly, rather than converting the
HTML preview to PDF — deliberately avoids WeasyPrint/wkhtmltopdf-style tools,
which need system libraries (Cairo, Pango, GTK) that are a common source of
setup pain on Windows. ReportLab is pure-Python with prebuilt wheels, so
`pip install` is all that's needed.
"""
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable

from app.services.result_service import compute_student_result, compute_class_ranking
from app.services.attendance_service import compute_attendance_stats


def build_report_card_pdf(exam, student, remark=None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=16, spaceAfter=2)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
    heading_style = ParagraphStyle("HeadingCustom", parent=styles["Heading3"], spaceBefore=10, spaceAfter=4)

    school = exam.school
    result = compute_student_result(exam, student.id)
    ranking = compute_class_ranking(exam)
    rank_entry = next((r for r in ranking if r["student"].id == student.id), None)
    attendance = compute_attendance_stats(student.id, session_id=exam.session_id)

    elements = [Paragraph(school.name, title_style)]
    contact_bits = [b for b in [school.address, school.phone, school.email] if b]
    if contact_bits:
        elements.append(Paragraph(" | ".join(contact_bits), subtitle_style))
    elements.append(Spacer(1, 4 * mm))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#333333")))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(f"Report Card &mdash; {exam.name}", heading_style))

    class_label = f"{student.current_class.name} - {student.current_section.name}" if student.current_class else "-"
    info_data = [
        ["Student Name:", student.name, "Admission No.:", student.admission_number],
        ["Class:", class_label, "Roll No.:", student.current_roll_number or "-"],
        ["Session:", exam.session.name, "Exam Dates:", f"{exam.start_date} to {exam.end_date}"],
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

    table_data = [["Subject", "Max Marks", "Passing Marks", "Obtained", "Result"]]
    for s in result["subjects"]:
        obtained_display = s["obtained_marks"] if s["obtained_marks"] is not None else "-"
        if s["passed"] is None:
            result_display = "Not Marked"
        else:
            result_display = "Pass" if s["passed"] else "Fail"
        table_data.append([s["subject"].name, str(s["max_marks"]), str(s["passing_marks"]), str(obtained_display), result_display])

    marks_table = Table(table_data, colWidths=[55 * mm, 30 * mm, 30 * mm, 25 * mm, 30 * mm])
    marks_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f3f5")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(marks_table)
    elements.append(Spacer(1, 6 * mm))

    summary_data = [
        ["Total Marks:", f"{result['total_obtained']} / {result['total_max']}" if result["total_max"] else "-"],
        ["Percentage:", f"{result['percentage']}%" if result["percentage"] is not None else "-"],
        ["Grade:", result["grade"] or "-"],
        ["Overall Result:", ("Pass" if result["overall_pass"] else "Fail") if result["overall_pass"] is not None else "-"],
        ["Class Position:", f"{rank_entry['rank']} of {len(ranking)}" if rank_entry else "-"],
        ["Attendance:", f"{attendance['percentage']}%" if attendance["percentage"] is not None else "-"],
    ]
    summary_table = Table(summary_data, colWidths=[40 * mm, 60 * mm])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("Teacher's Remarks", heading_style))
    elements.append(Paragraph((remark.teacher_remarks if remark and remark.teacher_remarks else "-"), styles["Normal"]))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph("Principal's Remarks", heading_style))
    elements.append(Paragraph((remark.principal_remarks if remark and remark.principal_remarks else "-"), styles["Normal"]))
    elements.append(Spacer(1, 14 * mm))

    sig_table = Table(
        [["_____________________", "_____________________", "_____________________"],
         ["Class Teacher", "Principal", "Parent/Guardian"]],
        colWidths=[55 * mm, 55 * mm, 55 * mm],
    )
    sig_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

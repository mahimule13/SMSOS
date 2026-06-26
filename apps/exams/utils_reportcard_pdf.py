import io
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

from apps.exams.models import StudentMarks



def _safe_float(val, default=0.0):
    try:
        if val is None:
            return default
        return float(val)
    except Exception:
        return default


def compute_reportcard_for_student_exam(student, exam):
    """Compute totals/percentage/grade from StudentMarks.

    Uses Exam.total_marks as max per subject (current project schema).
    """
    marks_qs = (
        StudentMarks.objects.filter(student=student, exam=exam)
        .select_related('subject', 'exam')
    )
    subject_marks = list(marks_qs)

    total_obtained = sum(_safe_float(m.marks_obtained) for m in subject_marks)
    num_subjects = len(subject_marks)

    # If no subjects entered, fall back to exam.total_marks to avoid division errors.
    denom = (num_subjects * _safe_float(exam.total_marks, 0.0)) if num_subjects else _safe_float(exam.total_marks, 0.0)
    percentage = (total_obtained / denom) * 100 if denom else 0

    # Grade logic aligned with StudentMarks.get_grade thresholds.
    if percentage >= 90:
        grade = 'A+'
    elif percentage >= 80:
        grade = 'A'
    elif percentage >= 70:
        grade = 'B+'
    elif percentage >= 60:
        grade = 'B'
    elif percentage >= 50:
        grade = 'C'
    else:
        grade = 'F'

    # Pass/Fail result based on exam.passing_marks
    total_marks = total_obtained
    result = 'Pass' if total_marks >= _safe_float(exam.passing_marks, 0.0) else 'Fail'

    return {
        'total_marks': total_marks,
        'percentage': percentage,
        'grade': grade,
        'result': result,
        'subjects': subject_marks,
    }


def build_reportcard_pdf_bytes(*, school_name, logo_path, student_details, exam_details, subject_rows, totals, remarks):
    """Create a basic but professional PDF using reportlab.

    Returns PDF bytes.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin_x = 1.5 * cm
    y = height - 2.0 * cm

    # Header
    c.setFont('Helvetica-Bold', 16)
    c.drawString(margin_x, y, school_name[:60])

    # Logo (optional)
    if logo_path and os.path.exists(logo_path):
        try:
            # Reserve space at top-right
            c.drawImage(logo_path, width - margin_x - 2.3 * cm, y - 0.2 * cm, width=2.3 * cm, height=2.3 * cm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    y -= 0.9 * cm
    c.setLineWidth(1)
    c.line(margin_x, y, width - margin_x, y)

    y -= 0.6 * cm

    # Student details
    c.setFont('Helvetica', 10.5)
    line1 = f"Student: {student_details.get('name','')} (ID: {student_details.get('student_id','')})"
    c.drawString(margin_x, y, line1)
    y -= 0.45 * cm

    c.setFont('Helvetica', 10.5)
    line2 = f"Class/Section: {student_details.get('class','')} / {student_details.get('section','')}   Roll No: {student_details.get('roll_no','')}"
    c.drawString(margin_x, y, line2)
    y -= 0.55 * cm

    # Exam details
    c.setFont('Helvetica-Bold', 11)
    c.drawString(margin_x, y, f"Report Card - {exam_details.get('exam_name','')}")
    y -= 0.45 * cm

    c.setFont('Helvetica', 10.5)
    c.drawString(margin_x, y, f"Exam Date: {exam_details.get('exam_date','')}    Total Marks: {exam_details.get('total_marks','')}")
    y -= 0.6 * cm

    # Table header
    c.setFont('Helvetica-Bold', 10)
    c.drawString(margin_x, y, 'Subject')
    c.drawString(margin_x + 8.8 * cm, y, 'Marks')
    c.drawString(margin_x + 13.2 * cm, y, 'Total')
    y -= 0.4 * cm

    c.setLineWidth(0.7)
    c.line(margin_x, y, width - margin_x, y)
    y -= 0.35 * cm

    # Table rows
    c.setFont('Helvetica', 10)
    row_height = 0.55 * cm
    for subject_name, marks_obtained, max_marks in subject_rows:
        if y < 4.0 * cm:
            c.showPage()
            y = height - 2.0 * cm
            c.setFont('Helvetica-Bold', 10)
            c.drawString(margin_x, y, 'Subject')
            c.drawString(margin_x + 8.8 * cm, y, 'Marks')
            c.drawString(margin_x + 13.2 * cm, y, 'Total')
            y -= 0.4 * cm
            c.setFont('Helvetica', 10)

        c.drawString(margin_x, y, str(subject_name)[:32])
        marks_str = f"{marks_obtained:.2f}"
        total_str = f"{max_marks:.2f}" if max_marks else ""
        c.drawString(margin_x + 8.8 * cm, y, marks_str)
        c.drawString(margin_x + 13.2 * cm, y, total_str)
        y -= row_height



    # Totals
    y -= 0.2 * cm
    c.setLineWidth(0.7)
    c.line(margin_x, y, width - margin_x, y)
    y -= 0.5 * cm

    c.setFont('Helvetica-Bold', 11)
    c.drawString(margin_x, y, 'Total & Result')
    y -= 0.45 * cm

    c.setFont('Helvetica', 10.5)
    c.drawString(margin_x, y, f"Total Marks: {totals.get('total_marks',0):.2f}")
    y -= 0.35 * cm
    c.drawString(margin_x, y, f"Percentage: {totals.get('percentage',0):.2f}%")
    y -= 0.35 * cm
    c.drawString(margin_x, y, f"Grade: {totals.get('grade','-')}")
    y -= 0.35 * cm
    c.drawString(margin_x, y, f"Result: {totals.get('result','-')}")

    # Remarks
    y -= 0.6 * cm
    c.setFont('Helvetica-Bold', 11)
    c.drawString(margin_x, y, 'Teacher Remarks')
    y -= 0.45 * cm

    c.setFont('Helvetica', 10.5)
    remarks_text = (remarks or '').strip() or '—'
    # Simple wrapping
    words = remarks_text.split()
    cur = ''
    lines = []
    for w in words:
        test = (cur + ' ' + w).strip()
        if c.stringWidth(test, 'Helvetica', 10.5) < (width - 2*margin_x):
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    for ln in lines[:8]:
        c.drawString(margin_x, y, ln)
        y -= 0.4 * cm

    # Footer signature block
    y -= 0.3 * cm
    c.setFont('Helvetica', 9.5)
    c.drawString(margin_x, 1.8 * cm, 'Signature')
    c.line(margin_x, 1.3 * cm, margin_x + 6 * cm, 1.3 * cm)

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
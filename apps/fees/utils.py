from reportlab.pdfgen import canvas
from django.conf import settings
import os


def generate_fee_receipt(receipt):

    folder = os.path.join(settings.MEDIA_ROOT, "receipts")

    os.makedirs(folder, exist_ok=True)

    file_name = f"{receipt.receipt_number}.pdf"

    file_path = os.path.join(folder, file_name)

    c = canvas.Canvas(file_path)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(180, 800, "SCHOOL FEE RECEIPT")

    c.setFont("Helvetica", 12)

    fee = receipt.fee_collection
    student = fee.student

    c.drawString(50, 740, f"Receipt No: {receipt.receipt_number}")
    c.drawString(50, 710, f"Student: {student.user.get_full_name()}")
    c.drawString(50, 680, f"Student ID: {student.student_id}")
    c.drawString(50, 650, f"Amount Paid: Rs.{fee.amount_paid}")
    c.drawString(50, 620, f"Payment Date: {fee.payment_date}")
    c.drawString(50, 590, f"Status: {fee.status}")

    c.drawString(50, 520, "Thank you for your payment.")

    c.save()

    return f"receipts/{file_name}"
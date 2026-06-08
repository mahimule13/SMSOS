from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from rest_framework import request
from apps.students.models import Student
from apps.accounts.ivr_service import make_call
from apps.accounts.services import send_bulk_sms



from apps.accounts.decorators import role_required
from apps.students.models import Student
from .utils import generate_fee_receipt
from .models import (
    FeeCollection,
    FeeStructure,
    FeeReceipt,
)
from decimal import Decimal
import datetime
from django.http import FileResponse, Http404
import os
from django.conf import settings
from urllib.parse import quote as urlquote
from django.views.decorators.clickjacking import xframe_options_exempt

# =========================
# FEE LIST
# =========================

@login_required(login_url='login')
@role_required('principal')
def fee_list(request):

    fees = FeeCollection.objects.all().order_by('-month')

    context = {
        'fees': fees
    }

    return render(
        request,
        'fees/list.html',
        context
    )


# =========================
# FEE COLLECTION
# =========================

@login_required(login_url='login')
@role_required('principal')
def fee_collection(request):

    if request.method == 'POST':

        fee_id = request.POST.get('fee_id')

        amount_paid = request.POST.get('amount_paid')

        payment_method = request.POST.get('payment_method')

        fee = get_object_or_404(
            FeeCollection,
            id=fee_id
        )

        try:
            amount_paid_value = Decimal(amount_paid)
            fee.amount_paid = Decimal(fee.amount_paid) + amount_paid_value

        except (TypeError, ValueError):
            fee.amount_paid = Decimal(0)

        fee.payment_method = payment_method

        if payment_method == 'bank_transfer':
            fee.account_number = request.POST.get('account_number', '').strip()
            fee.bank_name = request.POST.get('bank_name', '').strip()
            fee.ifsc_code = request.POST.get('ifsc_code', '').strip()

        fee.payment_date = datetime.date.today()


        if fee.amount_paid >= fee.amount_due:

            fee.status = 'paid'

        else:

            fee.status = 'partial'

        fee.collected_by = request.user

        fee.save()
        # Create receipt if not exists
        # Create receipt if not exists
        if not FeeReceipt.objects.filter(fee_collection=fee).exists():

            receipt_number = (
                f"REC{fee.id}"
                f"{datetime.date.today().strftime('%Y%m%d')}"
            )

            receipt = FeeReceipt.objects.create(
                fee_collection=fee,
                receipt_number=receipt_number,
                issued_by=request.user,
            )

            pdf_path = generate_fee_receipt(receipt)
            receipt.pdf_file = pdf_path
            receipt.save()
            print("PDF RECEIPT CREATED =", pdf_path)

        print("RECEIPT CREATED")
        student = fee.student

        parent_numbers = []

        if student.father_phone:
            parent_numbers.append(student.father_phone)

        if student.mother_phone:
            parent_numbers.append(student.mother_phone)

        remaining_amount = Decimal(fee.amount_due) - Decimal(fee.amount_paid)

        if remaining_amount > 0:

            message_text = (
            f"Dear Parent,\n"
            f"We received your fee payment successfully.\n"
            f"Student: {student.user.get_full_name()}\n"
            f"Paid Amount: Rs.{fee.amount_paid}\n"
            f"Pending Amount: Rs.{remaining_amount}\n"
            f"Please pay the remaining fee soon.\n"
            f"- School Management"
        )

        else:

            message_text = (
            f"Dear Parent,\n"
            f"Your fee payment was completed successfully.\n"
            f"Student: {student.user.get_full_name()}\n"
            f"Paid Amount: Rs.{fee.amount_paid}\n"
            f"No pending dues.\n"
            f"Thank you. Have a great day!\n"
            f"- School Management"
        )
        sms_result = send_bulk_sms(
            phones=parent_numbers,
            message=message_text
        )

        print("FEE SMS RESULT =", sms_result)
        messages.success(
            request,
            'Fee collected successfully'
        )

    pending_fees = FeeCollection.objects.filter(
        status__in=['pending', 'partial']
    ).order_by('-month')

    context = {
        'pending_fees': pending_fees
    }

    return render(
        request,
        'fees/collection.html',
        context
    )


# =========================
# FEE STRUCTURE
# =========================

@login_required(login_url='login')
@role_required('principal')
def fee_structure(request):

    if request.method == 'POST':

        class_name = request.POST.get(
            'class_name',
            ''
        ).strip()

        fee_type = request.POST.get(
            'fee_type',
            ''
        ).strip()

        amount = request.POST.get(
            'amount',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        # Validation
        if not class_name or not fee_type or not amount:

            messages.error(
                request,
                'Class Name, Fee Type and Amount are required.'
            )

        else:

            try:
                amount_value = float(amount)

            except (TypeError, ValueError):

                amount_value = None

            if amount_value is None:

                messages.error(
                    request,
                    'Invalid amount.'
                )

            else:

                # Create fee structure
                fee_structure_obj = FeeStructure.objects.create(
                    class_name=class_name,
                    fee_type=fee_type,
                    amount=amount_value,
                    description=description,
                )

                # =============================
                # AUTO CREATE STUDENT FEES
                # =============================

                students = Student.objects.filter(
                    section__class_model__standard=str(class_name)
                )

                created_count = 0

                for stu in students:

                    existing_fee = FeeCollection.objects.filter(
                        student_id=stu.id,
                        fee_structure=fee_structure_obj,
                        month=datetime.date.today().replace(day=1),
                    ).first()

                    if not existing_fee:

                        FeeCollection.objects.create(
                            student=stu,
                            fee_structure=fee_structure_obj,
                            month=datetime.date.today().replace(day=1),
                            amount_due=amount_value,
                            amount_paid=0,
                            status='pending',
                        )

                        created_count += 1

                messages.success(
                    request,
                    f'Fee structure added successfully. '
                    f'{created_count} student fee records created.'
                )

                return redirect('fees:structure')

    structures = FeeStructure.objects.all().order_by(
        'class_name',
        'fee_type'
    )

    context = {
        'structures': structures
    }

    return render(
        request,
        'fees/structure.html',
        context
    )

    structures = FeeStructure.objects.all().order_by(
        'class_name',
        'fee_type'
    )

    context = {
        'structures': structures
    }

    return render(
        request,
        'fees/structure.html',
        context
    )


# =========================
# FEE REPORTS
# =========================

@login_required(login_url='login')
@role_required('principal')
def fee_reports(request):

    total_due = (
        FeeCollection.objects.aggregate(
            Sum('amount_due')
        )['amount_due__sum']
        or 0
    )

    total_collected = (
        FeeCollection.objects.filter(
            status='paid'
        ).aggregate(
            Sum('amount_paid')
        )['amount_paid__sum']
        or 0
    )

    pending = (
        FeeCollection.objects.filter(
            status__in=['pending', 'partial']
        ).aggregate(
            Sum('amount_due')
        )['amount_due__sum']
        or 0
    )

    context = {
        'total_due': total_due,
        'total_collected': total_collected,
        'pending': pending,
    }

    return render(
        request,
        'fees/reports.html',
        context
    )


# =========================
# BUILD UPI URL
# =========================

# @login_required(login_url='login')
# @role_required('student')
def _build_upi_intent_url(
    *,
    amount: float,
    note: str = "Fee Payment"
):

    payee_vpa = getattr(
        settings,
        "UPI_PAYEE_VPA",
        "schoolms@upi"
    )

    payee_name = getattr(
        settings,
        "UPI_PAYEE_NAME",
        "SchoolMS Fees"
    )

    amount_str = f"{amount:.2f}"

    params = {
        "pa": payee_vpa,
        "pn": payee_name,
        "am": amount_str,
        "cu": "INR",
        "tn": note,
    }

    query = "&".join([
        f"{k}={urlquote(str(v))}"
        for k, v in params.items()
    ])

    return f"upi://pay?{query}"


# =========================
# STUDENT PAY
# =========================
@login_required(login_url='login')
@role_required('student')
def student_pay(request):

    student = request.user.student_profile

    pending_fees = FeeCollection.objects.filter(
        student=student,
        status__in=['pending', 'partial']
    ).order_by('-month')

    fees_history = FeeCollection.objects.filter(
        student=student
    ).order_by('-month')

    context = {
        'student': student,
        'fees': pending_fees,
        'fees_history': fees_history,
        'hide_payment_form': False,
    }

    # ---------------------------
    # GET REQUEST
    # ---------------------------
    if request.method == "GET":
        return render(request, "fees/student_pay.html", context)

    # ---------------------------
    # POST REQUEST
    # ---------------------------
    fee_id = request.POST.get('fee_id')
    amount_paid = request.POST.get('amount_paid')
    payment_method = request.POST.get('payment_method', 'cash')
    remarks = request.POST.get('remarks', '')

    if not fee_id:
        messages.error(request, "Please select a fee.")
        return redirect("fees:student_pay")

    fee = get_object_or_404(
        FeeCollection,
        id=fee_id,
        student=student
    )

    # ---------------------------
    # VALIDATE AMOUNT
    # ---------------------------
    try:
        amount_paid_value = Decimal(amount_paid)
    except:
        amount_paid_value = Decimal("0")

    if amount_paid_value <= 0:
        messages.error(request, "Please enter a valid amount.")
        return redirect("fees:student_pay")

    # ---------------------------
    # UPDATE FEE
    # ---------------------------
    fee.amount_paid = Decimal(fee.amount_paid) + amount_paid_value
    fee.payment_method = payment_method
    fee.payment_date = datetime.date.today()
    fee.remarks = remarks
    fee.collected_by = request.user

    if fee.amount_paid >= fee.amount_due:
        fee.amount_paid = fee.amount_due
        fee.status = "paid"
    else:
        fee.status = "partial"

    fee.save()

    # ---------------------------
    # RECEIPT
    # ---------------------------
    receipt, created = FeeReceipt.objects.get_or_create(
        fee_collection=fee,
        defaults={
            "receipt_number": f"REC{fee.id}{datetime.date.today().strftime('%Y%m%d')}",
            "issued_by": request.user
        }
    )

    pdf_path = generate_fee_receipt(receipt)
    receipt.pdf_file = pdf_path
    receipt.save()

    print("PDF RECEIPT CREATED =", pdf_path)

    # ---------------------------
    # SMS
    # ---------------------------
    parent_numbers = list(filter(None, [
        student.father_phone,
        student.mother_phone
    ]))

    remaining_amount = fee.amount_due - fee.amount_paid

    if remaining_amount > 0:
        message_text = (
            f"Dear Parent,\n"
            f"Fee payment received successfully.\n"
            f"Student: {student.user.get_full_name()}\n"
            f"Paid: Rs.{amount_paid_value}\n"
            f"Pending: Rs.{remaining_amount}\n"
            f"- School Management"
        )
    else:
        message_text = (
            f"Dear Parent,\n"
            f"Fee fully paid.\n"
            f"Student: {student.user.get_full_name()}\n"
            f"Paid: Rs.{amount_paid_value}\n"
            f"No pending dues.\n"
            f"- School Management"
        )

    sms_result = send_bulk_sms(
        phones=parent_numbers,
        message=message_text
    )

    print("SMS RESULT =", sms_result)

    # ---------------------------
    # UPI FLOW
    # ---------------------------
    if payment_method == "upi":

        upi_url = _build_upi_intent_url(
            amount=amount_paid_value,
            note=f"{fee.fee_structure.class_name} {fee.fee_structure.fee_type}"
        )

        messages.success(request, "Payment recorded successfully.")

        return render(
            request,
            "fees/student_pay.html",
            {
                **context,
                "upi_url": upi_url,
                "show_upi_id_prompt": True,
                "upi_notice": "UPI payment initiated successfully."
            }
        )

    messages.success(request, "Payment recorded successfully.")
    return redirect("fees:student_pay")
def download_receipt(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)

    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf', )
    raise Http404("Receipt not found")
@xframe_options_exempt  # Allows the PDF to load safely inside the iframe
def receipt_preview(request, filename):
    # 1. Build the absolute path to where the file lives on your disk
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    
    # 2. Check if the file actually exists
    if os.path.exists(file_path):
        # Open the file in binary read mode
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        
        # 'inline' tells the browser to display it on screen rather than downloading it
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(filename)}"'
        return response
        
    raise Http404("Receipt file not found on disk.")

    def fee_pending_calls(request):
        students = Student.objects.filter(
        fee_pending=True
    )

    for student in students:

        make_call(

            student.parent_phone,

            "Dear Parent, your child fee payment is pending. Please pay immediately."
        )

    return redirect("teacher_dashboard")

# def fee_pending_calls(request):

#     students = Student.objects.filter(
#         fee_pending=True
#     )

#     for student in students:

#         make_call(

#             student.parent_phone,

#             "Dear Parent, your child fee payment is pending. Please pay immediately."
#         )

#     return redirect("teacher_dashboard")

# def absent_calls(request):

#     students = Student.objects.filter(
#         attendance_status="Absent"
#     )

#     for student in students:

#         make_call(

#             student.parent_phone,

#             "Dear Parent, your child is absent today."
#         )

#     return redirect("teacher_dashboard")

# def general_calls(request):
#     students = Student.objects.all()

#     for student in students:

#         make_call(

#             student.parent_phone,

#             "Tomorrow school holiday due to maintenance."
#         )

#     return redirect("teacher_dashboard")  
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from apps.accounts.decorators import admin_required, role_required
from .models import FeeCollection, FeeStructure, FeeReceipt
from apps.students.models import Student
import datetime
from django.conf import settings
from urllib.parse import quote




@login_required(login_url='login')
@role_required('principal')
def fee_list(request):
    fees = FeeCollection.objects.all().order_by('-month')
    context = {'fees': fees}
    return render(request, 'fees/list.html', context)


@login_required(login_url='login')
@role_required('principal')
def fee_collection(request):
    if request.method == 'POST':
        fee_id = request.POST.get('fee_id')
        amount_paid = request.POST.get('amount_paid')
        payment_method = request.POST.get('payment_method')
        
        fee = FeeCollection.objects.get(id=fee_id)
        ffee.amount_paid = float(fee.amount_paid) + float(amount_paid)
        fee.payment_method = payment_method
        fee.payment_date = datetime.date.today()
        
        if fee.amount_paid >= fee.amount_due:
            fee.status = 'paid'
        else:
            fee.status = 'partial'
        
        fee.collected_by = request.user
        fee.save()
        
        # Create receipt
        receipt_number = f"REC{fee.id}{datetime.date.today().strftime('%Y%m%d')}"
        FeeReceipt.objects.create(
            fee_collection=fee,
            receipt_number=receipt_number,
            issued_by=request.user
        )
        
        messages.success(request, 'Fee collected successfully')
    
    pending_fees = FeeCollection.objects.filter(
        status__in=['pending', 'partial']
    ).order_by('-month')
    
    context = {'pending_fees': pending_fees}
    return render(request, 'fees/collection.html', context)


@login_required(login_url='login')
@role_required('principal')
def fee_structure(request):
    structures
    context = {'structures': structures}
    return render(request, 'fees/structure.html', context)


@login_required(login_url='login')
@role_required('principal')
def fee_reports(request):
    # Financial summary
    total_due = FeeCollection.objects.aggregate(Sum('amount_due'))['amount_due__sum'] or 0
    total_collected = FeeCollection.objects.filter(status='paid').aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    pending = FeeCollection.objects.filter(status__in=['pending', 'partial']).aggregate(Sum('amount_due'))['amount_due__sum'] or 0

    context = {
        'total_due': total_due,
        'total_collected': total_collected,
        'pending': pending,
    }
    return render(request, 'fees/reports.html', context)


@login_required(login_url='login')
@role_required('student')
def _build_upi_intent_url(*, amount: float, note: str = "Fee Payment"):
    # UPI intent using the standard "upi://pay" deep link.
    # This launches the UPI app; final payment confirmation requires provider/webhook.
    payee_vpa = getattr(settings, "UPI_PAYEE_VPA", "schoolms@upi")
    payee_name = getattr(settings, "UPI_PAYEE_NAME", "SchoolMS Fees")

    # amount param in UPI links should be a string; keep 2 decimals.
    amount_str = f"{amount:.2f}"

    # Build query parameters.
    # Example: upi://pay?pa=xxx&pn=yyy&am=10.00&cu=INR&tn=Fee%20Payment
    params = {
        "pa": payee_vpa,
        "pn": payee_name,
        "am": amount_str,
        "cu": "INR",
        "tn": note,
    }
    # urlquote each value to keep spaces/special chars safe
    query = "&".join([f"{k}={urlquote(str(v))}" for k, v in params.items()])
    return f"upi://pay?{query}"



@login_required(login_url='login')
@role_required('student')
def student_pay(request):

    student = request.user.student_profile



    pending_fees = FeeCollection.objects.filter(
        student=student,
        status__in=['pending', 'partial'],
    ).order_by('-month')

    context = {
        'student': student,
        'fees': pending_fees,
    }

    if not pending_fees.exists():
        return render(request, 'fees/student_pay.html', context)

    if request.method == 'POST':
        fee_id = request.POST.get('fee_id')
        amount_paid = request.POST.get('amount_paid')
        payment_method = request.POST.get('payment_method')

        fee = get_object_or_404(
            FeeCollection,
            id=fee_id,
            student=student,
        )

        try:
            amount_paid_value = float(amount_paid)
        except (TypeError, ValueError):
            amount_paid_value = 0

        if amount_paid_value <= 0:
            messages.error(request, 'Please enter a valid amount.')
            return render(request, 'fees/student_pay.html', context)

        # If student selected UPI, launch the UPI app using upi://pay.
        # Note: without PSP webhook/provider integration we can't reliably mark as "paid" here.
        if payment_method == 'upi':
            upi_url = _build_upi_intent_url(
                amount=amount_paid_value,
                note=f"{fee.fee_structure.name} fee for {fee.month.strftime('%B %Y')}",
            )
            # Redirect the browser to the UPI app.
            # We set current fields as a "recorded attempt" (optional), but we keep status unchanged
            # unless you want auto-marking. We'll keep status as-is.
            fee.payment_method = payment_method
            fee.payment_date = datetime.date.today()
            fee.remarks = request.POST.get('remarks', '')
            fee.collected_by = request.user
            fee.save()

            # Meta refresh acts like a redirect without breaking CSRF flow.
            context = {
                'upi_url': upi_url,
            }
            return render(request, 'fees/student_pay.html', {
                **context,
                'student': student,
                'fees': pending_fees,
                'hide_payment_form': True,
                'upi_notice': 'Opening UPI payment...'
            })

        # Non-UPI: record payment immediately.
        fee.amount_paid = float(fee.amount_paid) + amount_paid_value
        fee.payment_method = payment_method
        fee.payment_date = datetime.date.today()
        fee.remarks = request.POST.get('remarks', '')
        fee.collected_by = request.user

        if payment_method == 'bank_transfer':
            fee.account_number = request.POST.get('account_number', '').strip()
            fee.bank_name = request.POST.get('bank_name', '').strip()
            fee.ifsc_code = request.POST.get('ifsc_code', '').strip()


        if fee.amount_paid >= fee.amount_due:
            fee.amount_paid = fee.amount_due
            fee.status = 'paid'
        else:
            fee.status = 'partial'

        fee.save()

        if not hasattr(fee, 'receipt'):

            receipt_number = f"REC{fee.id}{datetime.date.today().strftime('%Y%m%d')}"
            FeeReceipt.objects.create(
                fee_collection=fee,
                receipt_number=receipt_number,
                issued_by=request.user,
            )

        messages.success(request, 'Payment recorded successfully.')
        return redirect('fees:student_pay')

    return render(request, 'fees/student_pay.html', context)


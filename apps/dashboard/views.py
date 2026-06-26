from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg, Q
from django.urls import reverse
import urllib.parse
from datetime import date, timedelta
from calendar import monthrange
from apps.accounts.decorators import role_required
from apps.transport.models import Bus, StudentTransport
from apps.students.models import Student, StudentAttendance
from apps.teachers.models import (
    Teacher,
    TeacherAttendance,
    TeacherLeaveRequest,
)
from apps.fees.models import FeeCollection
from apps.exams.models import (
    StudentMarks,
    ReportCard,
    Exam,
    ExamSchedule,
)

from apps.classes.models import (
    ClassModel,
    Section,
    Subject
)
from apps.homework.models import Homework, StudentSubmission
from apps.fees.models import FeeCollection as StudentFeeCollection
from apps.library.models import (
    BookIssue,
    Book
)
from apps.transport.models import Bus, BusDriver, StudentTransport, BusRoute
from apps.hostel.models import HostelAllocation
from apps.finance.models import (
    Income,
    Expense,
    ExpenseCategory,
)
from apps.noticeboard.models import (
    Notice,
    Event
)
from apps.timetable.models import Timetable
from apps.transport.models import Bus, BusDriver
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
import json


# =========================================================
# COMMON DASHBOARD CONTEXT
# =========================================================

def get_dashboard_context(request):


    context = {}

    # =====================================
    # USER PROFILE
    # =====================================

    try:
        user_profile = request.user.profile
        context['user_profile'] = user_profile

    except Exception:
        context['user_profile'] = None

    # =====================================
    # NOTICES & EVENTS
    # =====================================

    context['notices'] = Notice.objects.filter(
        is_active=True
    ).order_by('-created_at')[:5]

    context['events'] = Event.objects.filter(
        is_active=True
    ).order_by('-event_date')[:5]

    # =====================================
    # GLOBAL COUNTS
    # =====================================

    context['total_students'] = Student.objects.filter(
        is_active=True
    ).count()

    context['total_teachers'] = Teacher.objects.filter(
        is_active=True
    ).count()

    context['total_classes'] = ClassModel.objects.filter(
        is_active=True
    ).count()

    context['total_sections'] = Section.objects.filter(
        is_active=True
    ).count()

    context['total_subjects'] = Subject.objects.filter(
        is_active=True
    ).count()

    # =====================================
    # ATTENDANCE
    # =====================================

    today = date.today()

    students_present = StudentAttendance.objects.filter(
        date=today,
        is_present=True
    ).values('student_id').distinct().count()

    students_absent = StudentAttendance.objects.filter(
        date=today,
        is_present=False
    ).values('student_id').distinct().count()

    total_students = Student.objects.filter(
        is_active=True
    ).count()

    attendance_percentage = 0

    if total_students > 0:

        attendance_percentage = (

            students_present / total_students

        ) * 100


    context['students_present'] = students_present
    context['students_absent'] = students_absent

    context['attendance_percentage'] = round(
        attendance_percentage,
        2
    )

    # =====================================
    # FEES
    # =====================================

    total_fee_due = FeeCollection.objects.filter(
        status__in=['pending', 'partial']
    ).aggregate(
        Sum('amount_due')
    )['amount_due__sum'] or 0

    total_fee_collected = FeeCollection.objects.filter(
        status='paid'
    ).aggregate(
        Sum('amount_paid')
    )['amount_paid__sum'] or 0

    current_month_collected = FeeCollection.objects.filter(
        status='paid',
        payment_date__year=today.year,
        payment_date__month=today.month
    ).aggregate(
        Sum('amount_paid')
    )['amount_paid__sum'] or 0

    context['total_fee_due'] = float(total_fee_due)

    context['total_fee_collected'] = float(
        total_fee_collected
    )

    context['current_month_collected'] = float(
        current_month_collected
    )

    context['pending_fees'] = float(
        total_fee_due
    )

    # =====================================
    # EXAMS
    # =====================================

    current_exam = Exam.objects.filter(
        is_active=True
    ).first()

    if current_exam:

        context['current_exam'] = current_exam

        avg_marks = StudentMarks.objects.filter(
            exam=current_exam
        ).aggregate(
            Avg('marks_obtained')
        )['marks_obtained__avg'] or 0

        context['exam_avg_marks'] = round(
            avg_marks,
            2
        )

    # =====================================
    # RECENT STUDENTS
    # =====================================

    context['recent_students'] = Student.objects.filter(
        is_active=True
    ).order_by('-created_at')[:6]

    # =====================================
    # TEACHER ATTENDANCE
    # =====================================

    teacher_present_today = TeacherAttendance.objects.filter(
        date=today,
        is_present=True
    ).count()

    total_teachers = Teacher.objects.filter(
        is_active=True
    ).count()

    teacher_absent_today = max(0, total_teachers - teacher_present_today)

    teacher_attendance_percentage = 0

    if total_teachers > 0:

        teacher_attendance_percentage = (
            teacher_present_today / total_teachers
        ) * 100

    context['teacher_present_today'] = teacher_present_today
    context['teacher_absent_today'] = teacher_absent_today
    context['teacher_attendance_percentage'] = round(
        teacher_attendance_percentage,
        2
    )

    return context


# =========================================================
# ATTENDANCE REPORT HELPERS
# =========================================================

def get_monthly_attendance_report_context(request):
    report_month = request.GET.get('report_month', '')
    report_class_id = request.GET.get('report_class_id', '').strip()

    try:
        if report_month:
            year, month = [int(x) for x in report_month.split('-')]
            selected_month_date = date(year, month, 1)
        else:
            today = date.today()
            selected_month_date = today.replace(day=1)
            report_month = selected_month_date.strftime('%Y-%m')
    except Exception:
        today = date.today()
        selected_month_date = today.replace(day=1)
        report_month = selected_month_date.strftime('%Y-%m')

    report_month_label = selected_month_date.strftime('%B %Y')
    days_in_month = monthrange(selected_month_date.year, selected_month_date.month)[1]

    class_qs = ClassModel.objects.filter(is_active=True).order_by('standard')
    if report_class_id.isdigit():
        class_qs = class_qs.filter(pk=int(report_class_id))

    class_attendance_report = []
    for cls in class_qs:
        student_count = Student.objects.filter(
            section__class_model=cls,
            is_active=True
        ).count()
        attendance_qs = StudentAttendance.objects.filter(
            student__section__class_model=cls,
            date__year=selected_month_date.year,
            date__month=selected_month_date.month
        )
        present_count = attendance_qs.filter(is_present=True).count()
        total_records = attendance_qs.count()
        average_percentage = round((present_count / total_records) * 100, 2) if total_records else 0
        class_attendance_report.append({
            'class_name': str(cls),
            'student_count': student_count,
            'present_count': present_count,
            'total_records': total_records,
            'average_percentage': average_percentage,
            'expected_records': student_count * days_in_month,
        })

    teacher_qs = TeacherAttendance.objects.filter(
        date__year=selected_month_date.year,
        date__month=selected_month_date.month
    )
    teacher_present = teacher_qs.filter(is_present=True).count()
    teacher_records = teacher_qs.count()
    teacher_total = Teacher.objects.filter(is_active=True).count()
    teacher_monthly_percentage = round((teacher_present / teacher_records) * 100, 2) if teacher_records else 0

    return {
        'selected_report_month': report_month,
        'report_month_label': report_month_label,
        'report_class_id': report_class_id,
        'class_attendance_report': class_attendance_report,
        'teacher_monthly_present': teacher_present,
        'teacher_monthly_records': teacher_records,
        'teacher_monthly_percentage': teacher_monthly_percentage,
        'teacher_attendance_total': teacher_total,
    }


# =========================================================
# HOME REDIRECT
# =========================================================

@login_required(login_url='accounts:login')
def home_redirect(request):

    try:

        profile = request.user.profile
        role = profile.role

        print("USER :", request.user.username)
        print("ROLE :", role)

        # =====================================
        # ADMIN
        # =====================================

        if role in ['super_admin', 'school_admin']:

            return redirect(
                'dashboard:admin_dashboard'
            )

        # =====================================
        # PRINCIPAL
        # =====================================

        elif role == 'principal':

            return redirect(
                'dashboard:principal_dashboard'
            )

        # =====================================
        # TEACHER
        # =====================================

        elif role == 'teacher':

            return redirect(
                'dashboard:teacher_dashboard'
            )

        # =====================================
        # STUDENT
        # =====================================

        elif role == 'student':

            return redirect(
                'dashboard:student_dashboard'
            )

        # =====================================
        # ACCOUNTANT
        # =====================================

        elif role == 'accountant':

            return redirect(
                'dashboard:accountant_dashboard'
            )

        # =====================================
        # LIBRARIAN
        # =====================================

        elif role == 'librarian':

            return redirect(
                'dashboard:librarian_dashboard'
            )

        # =====================================
        # DEFAULT
        # =====================================

        return redirect('accounts:profile')

    except Exception as e:

        print("HOME REDIRECT ERROR :", e)

        return redirect('accounts:login')


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@login_required(login_url='accounts:login')
@role_required('super_admin', 'school_admin')
def admin_dashboard(request):

    context = get_dashboard_context(request)
    context['classes'] = ClassModel.objects.filter(
        is_active=True
    ).order_by('standard')
    context.update(get_monthly_attendance_report_context(request))

    # ---------------------------------------------------------
    # Charts Data (Chart.js)
    # ---------------------------------------------------------

    # Attendance Trend (Last 7 Days)
    attendance_data = []
    for i in range(7, 0, -1):
        current_date = date.today() - timedelta(days=i)
        attendance_count = StudentAttendance.objects.filter(
            date=current_date,
            is_present=True
        ).count()
        attendance_data.append({
            'date': current_date.strftime('%m-%d'),
            'present': attendance_count
        })
    context['attendance_data'] = json.dumps(attendance_data)

    # Fee Collection (Last 6 Months)
    fee_data = []
    for i in range(5, -1, -1):
        month_start = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)  # dummy, corrected below
        # Compute month start properly
        tmp = date.today().replace(day=1) - timedelta(days=1)
        # Shift i months back from current month start
    
    # safer month iteration
    from calendar import monthrange
    today = date.today()
    current_month_start = today.replace(day=1)
    def shift_month(d, months):
        y = d.year + (d.month - 1 + months) // 12
        m = (d.month - 1 + months) % 12 + 1
        return d.replace(year=y, month=m, day=1)

    for i in range(5, -1, -1):
        m_start = shift_month(current_month_start, -i)
        m_end = shift_month(m_start, 1) - timedelta(days=1)
        collected = FeeCollection.objects.filter(
            status='paid',
            payment_date__gte=m_start,
            payment_date__lte=m_end,
        ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        fee_data.append({
            'month': m_start.strftime('%b %Y'),
            'collected': float(collected)
        })
    context['fee_data'] = json.dumps(fee_data)

    # Class Distribution (count by standard/class)
    class_distribution_data = []
    class_qs = ClassModel.objects.filter(is_active=True).annotate(student_count=Count('sections__students'))
    for c in class_qs:
        class_distribution_data.append({
            'class': str(c.standard) if hasattr(c, 'standard') else str(c),
            'count': int(getattr(c, 'student_count', 0) or 0)
        })
    context['class_distribution_data'] = json.dumps(class_distribution_data)

    # Teacher Attendance (Last 7 Days)
    teacher_attendance_data = []
    for i in range(7, 0, -1):
        current_date = date.today() - timedelta(days=i)
        teacher_present = TeacherAttendance.objects.filter(
            date=current_date,
            is_present=True
        ).count()
        teacher_attendance_data.append({
            'date': current_date.strftime('%m-%d'),
            'present': teacher_present
        })
    context['teacher_attendance_data'] = json.dumps(teacher_attendance_data)

    # Teacher Gender Distribution
    teacher_gender_data = []
    for label in ['Male', 'Female', 'Other']:
        # tries to use teacher.user.profile.gender if available; fallback to 0
        try:
            count = Teacher.objects.filter(user__profile__gender=label, is_active=True).count()
        except Exception:
            count = 0
        teacher_gender_data.append({'label': label, 'count': int(count)})
    context['teacher_gender_data'] = json.dumps(teacher_gender_data)

    # Expense summary and transport details
    expense_fuel_qs = Expense.objects.filter(category__name__icontains='fuel')
    expense_transport_qs = Expense.objects.filter(category__name__icontains='transport')
    expense_other_qs = Expense.objects.exclude(category__name__icontains='fuel').exclude(category__name__icontains='transport')

    context['fuel_expense_total'] = expense_fuel_qs.aggregate(total=Sum('amount'))['total'] or 0
    context['transport_expense_total'] = expense_transport_qs.aggregate(total=Sum('amount'))['total'] or 0
    context['other_expense_total'] = expense_other_qs.aggregate(total=Sum('amount'))['total'] or 0
    context['other_expense_records'] = expense_other_qs.order_by('-date')[:10]
    context['recent_expense_records'] = Expense.objects.order_by('-date')[:10]

    transport_buses = Bus.objects.filter(is_active=True).select_related('driver', 'teacher')
    context['transport_bus_count'] = transport_buses.count()
    context['transport_driver_count'] = BusDriver.objects.filter(is_active=True).count()
    context['transport_buses'] = transport_buses.order_by('number')[:8]
    context['transport_assignments'] = StudentTransport.objects.filter(is_active=True).select_related('student__user', 'bus__driver', 'route')[:12]

    # Section filter (template uses these)
    context['sections'] = Section.objects.all()
    context['selected_section'] = request.GET.get('section', '')

    # Student search filter data for the dashboard template
    student_search_query = request.GET.get('student_search_query', '').strip()
    student_class_id = request.GET.get('student_class_id', '').strip()
    context['student_search_query'] = student_search_query
    context['student_class_id'] = student_class_id
    context['student_search_results'] = []

    if student_search_query or student_class_id:
        student_filters = Q(is_active=True)
        if student_search_query:
            search_text = student_search_query.strip()
            student_filters &= (
                Q(student_id__iexact=search_text) |
                Q(admission_number__iexact=search_text) |
                Q(user__username__iexact=search_text) |
                Q(user__first_name__iexact=search_text) |
                Q(user__last_name__iexact=search_text)
            )
            name_parts = search_text.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]
                student_filters |= (
                    Q(user__first_name__iexact=first_name) &
                    Q(user__last_name__iexact=last_name)
                )
        if student_class_id and student_class_id.isdigit():
            student_filters &= Q(section__class_model_id=int(student_class_id))

        context['student_search_results'] = (
            Student.objects.filter(student_filters)
            .select_related('user', 'section', 'section__class_model')
            .order_by('section__class_model__standard', 'section__name', 'roll_number')
        )

    # Optional template variables referenced in admin_dashboard.html
    context.setdefault('pending_fee_students', 0)
    context.setdefault('upcoming_birthdays', [])
    context.setdefault('top_pending_fees', [])

    return render(
        request,
        'dashboard/admin_dashboard.html',
        context
    )


@login_required(login_url='accounts:login')
@role_required('super_admin', 'school_admin', 'principal')
def expenses_panel(request):
    """Admin expenses panel: add fuel/transport/other expenses and view history."""
    from apps.finance.models import Expense, ExpenseCategory

    if request.method == 'POST' and request.POST.get('action') == 'add_expense':
        category_name = request.POST.get('category', 'Fuel').strip()
        amount_text = request.POST.get('amount', '0').strip()
        date_text = request.POST.get('date', '').strip()
        description = request.POST.get('description', '').strip()
        bill_attachment = request.FILES.get('bill_attachment')

        if not amount_text or not date_text or not description:
            messages.error(request, 'Please provide amount, date and description.')
            return redirect('dashboard:admin_expenses')

        try:
            from decimal import Decimal
            expense_date = date.fromisoformat(date_text)
            amount_val = Decimal(amount_text)
            category, _ = ExpenseCategory.objects.get_or_create(name=category_name)
            voucher_number = f"EXP-{category.name[:3].upper()}-{date.today().strftime('%Y%m%d%H%M%S')}"
            Expense.objects.create(
                category=category,
                amount=amount_val,
                description=description,
                date=expense_date,
                voucher_number=voucher_number,
                bill_attachment=bill_attachment,
                paid_by=request.user,
            )
            messages.success(request, 'Expense recorded successfully.')
        except Exception:
            messages.error(request, 'Unable to save expense. Please check the form and try again.')

        return redirect('dashboard:admin_expenses')

    expense_type = request.GET.get('type', 'all')
    expense_qs = Expense.objects.select_related('category', 'paid_by').exclude(category__name__icontains="transport").order_by('-date')
    if expense_type == 'fuel':
        expense_qs = expense_qs.filter(category__name__icontains='fuel')
    elif expense_type == 'other':
        expense_qs = expense_qs.exclude(category__name__icontains='fuel').exclude(category__name__icontains='transport')

    today = date.today()
    context = get_dashboard_context(request)
    context.update({
        'expense_history': expense_qs[:50],
        'expense_type': expense_type,
        'expense_categories': ['Fuel', 'Other'],
        'today': today,
    })
    return render(request, 'dashboard/expenses_panel.html', context)


@login_required(login_url='accounts:login')
@role_required('super_admin', 'school_admin')
def api_teacher_salary(request, teacher_id):
    """Return basic salary info for a teacher (JSON)."""
    from apps.teachers.models import Teacher
    try:
        t = Teacher.objects.select_related('user').get(pk=int(teacher_id))
        return JsonResponse({'ok': True, 'teacher_id': t.id, 'name': t.user.get_full_name(), 'base_salary': float(t.base_salary)})
    except Exception:
        return JsonResponse({'ok': False}, status=404)


# =========================================================
# PRINCIPAL DASHBOARD
# =========================================================

@login_required(login_url='accounts:login')
@role_required('principal')
def principal_dashboard(request):

    # Handle "Publish" announcement coming from principal dashboard.
    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'add_expense':
            category_name = request.POST.get('category', '').strip() or 'Fuel'
            amount_text = request.POST.get('amount', '').strip()
            expense_date_text = request.POST.get('date', '').strip()
            description = request.POST.get('description', '').strip()
            bill_attachment = request.FILES.get('bill_attachment')

            if not amount_text or not expense_date_text or not description:
                messages.error(request, 'Please provide category, amount, date and bill details.')
            else:
                try:
                    from decimal import Decimal
                    expense_date = date.fromisoformat(expense_date_text)
                    amount_val = Decimal(amount_text)
                    category, _ = ExpenseCategory.objects.get_or_create(name=category_name)
                    voucher_number = f"EXP-{category.name[:3].upper()}-{date.today().strftime('%Y%m%d%H%M%S')}"
                    Expense.objects.create(
                        category=category,
                        amount=amount_val,
                        description=description,
                        date=expense_date,
                        voucher_number=voucher_number,
                        bill_attachment=bill_attachment,
                        paid_by=request.user,
                    )
                    messages.success(request, 'Expense recorded successfully.')
                except Exception:
                    messages.error(request, 'Failed to save expense. Check the values and try again.')

            return redirect('dashboard:principal_dashboard')

        if action == 'add_transport_details':
            bus_number = request.POST.get('bus_number', '').strip()
            driver_name = request.POST.get('driver_name', '').strip()
            route_text = request.POST.get('route', '').strip()

            if not bus_number or not driver_name or not route_text:
                messages.error(request, 'Please provide bus number, driver name, and route for transport details.')
            else:
                try:
                    # Ensure Bus exists
                    bus, created = Bus.objects.get_or_create(
                        number=bus_number,
                        defaults={
                            'capacity': 20,
                            'model': '',
                            'registration_date': date.today(),
                            'is_active': True,
                        }
                    )
                    if not bus.is_active:
                        bus.is_active = True
                        bus.save()

                    # Ensure BusRoute exists for this bus
                    route, _ = BusRoute.objects.get_or_create(
                        bus=bus,
                        route_name=route_text,
                        defaults={'start_point': '', 'end_point': '', 'distance': 0, 'fare': 0}
                    )

                    # Link or create driver
                    driver = BusDriver.objects.filter(name__iexact=driver_name).first()
                    if driver:
                        driver.bus = bus
                        driver.is_active = True
                        driver.save()
                    else:
                        # create a placeholder driver with generated license and expiry
                        gen_license = f"GEN-{date.today().strftime('%Y%m%d%H%M%S')}"
                        license_expiry = date.today() + timedelta(days=365)
                        driver = BusDriver.objects.create(
                            name=driver_name,
                            phone='',
                            license_number=gen_license,
                            license_expiry=license_expiry,
                            bus=bus,
                            is_active=True
                        )

                    messages.success(request, 'Transport models created/updated successfully.')
                    # Redirect to principal transport list and show created items
                    params = {
                        'created_bus': bus.id,
                        'created_driver': driver.id if driver else '',
                        'created_route': route.id if route else ''
                    }
                    url = reverse('#') + '?' + urllib.parse.urlencode(params)
                    return redirect(url)
                except Exception:
                    messages.error(request, 'Unable to save transport details into transport models. Please try again.')

            return redirect('dashboard:principal_dashboard')

        title = request.POST.get('title', '').strip()
        priority = request.POST.get('priority', 'medium').strip()
        content = request.POST.get('content', '').strip()
        section_name = request.POST.get('section_name', '').strip()
        class_id = request.POST.get('class_id', '').strip()

        if title and content:
            Notice.objects.create(
                title=title,
                priority=priority if priority else 'medium',
                content=content,
                created_by=request.user,
                is_active=True,
            )
            messages.success(request, 'Announcement published successfully.')

        if section_name and class_id and class_id.isdigit():
            class_obj = ClassModel.objects.filter(pk=class_id, is_active=True).first()
            if class_obj:
                section, created = Section.objects.get_or_create(
                    class_model=class_obj,
                    name=section_name,
                    defaults={'is_active': True}
                )
                if created:
                    messages.success(request, f'Section "{section_name}" added to {class_obj}.')
                else:
                    messages.info(request, f'Section "{section_name}" already exists for {class_obj}.')
            else:
                messages.error(request, 'Please select a valid class to add a section.')

        return redirect('dashboard:principal_dashboard')

    context = get_dashboard_context(request)

    context['classes'] = ClassModel.objects.filter(
        is_active=True
    ).order_by('standard')
    context.update(get_monthly_attendance_report_context(request))

    # Student search filter for dashboard cards
    student_search_query = request.GET.get('student_search_query', '').strip()
    student_class_id = request.GET.get('student_class_id', '').strip()
    context['student_search_query'] = student_search_query
    context['student_class_id'] = student_class_id
    context['student_search_results'] = []

    if student_search_query or student_class_id:
        student_filters = Q(is_active=True)
        if student_search_query:
            search_text = student_search_query.strip()
            student_filters &= (
                Q(student_id__iexact=search_text) |
                Q(admission_number__iexact=search_text) |
                Q(user__username__iexact=search_text) |
                Q(user__first_name__iexact=search_text) |
                Q(user__last_name__iexact=search_text)
            )
            # Support full name matching when the user enters both parts.
            name_parts = search_text.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]
                student_filters |= (
                    Q(user__first_name__iexact=first_name) &
                    Q(user__last_name__iexact=last_name)
                )
        if student_class_id and student_class_id.isdigit():
            student_filters &= Q(section__class_model_id=int(student_class_id))

        context['student_search_results'] = (
            Student.objects.filter(student_filters)
            .select_related('user', 'section', 'section__class_model')
            .order_by('section__class_model__standard', 'section__name', 'roll_number')
        )

    student_fee_query = request.GET.get('student_fee_query', '').strip()
    context['student_fee_query'] = student_fee_query
    context['fee_search_results'] = []

    if student_fee_query:
        search_query = (
            Q(student__student_id__icontains=student_fee_query) |
            Q(student__admission_number__icontains=student_fee_query) |
            Q(student__user__first_name__icontains=student_fee_query) |
            Q(student__user__last_name__icontains=student_fee_query) |
            Q(student__user__username__icontains=student_fee_query) |
            Q(student__user__email__icontains=student_fee_query)
        )

        context['fee_search_results'] = (
            FeeCollection.objects.select_related(
                'student',
                'student__user',
                'student__section',
                'student__section__class_model',
                'fee_structure'
            )
            .filter(search_query)
            .order_by('-month')
        )

    recent_marks = StudentMarks.objects.select_related(
        'student',
        'exam',
        'subject'
    ).order_by('-created_at')[:10]

    context['recent_marks'] = recent_marks

    pending_leaves = TeacherLeaveRequest.objects.filter(
        status='pending'
    )

    context['pending_leave_requests'] = pending_leaves

    context['pending_leave_count'] = pending_leaves.count()

    context['expense_categories'] = ExpenseCategory.objects.all().order_by('name')
    context['today'] = date.today()
    context['recent_expenses'] = Expense.objects.order_by('-date')[:10]

    return render(
        request,
        'dashboard/principal_dashboard.html',
        context
    )
# =========================================================
# TEACHER DASHBOARD
# =========================================================

@login_required(login_url='accounts:login')
@role_required('teacher')
def teacher_dashboard(request):

    try:
        teacher = request.user.teacher_profile
    except Exception:
        return redirect('accounts:profile')

    context = get_dashboard_context(request)

    context['teacher'] = teacher

    context['subject_allocations'] = (
        teacher.subject_allocations.all()
    )

    context['active_homework'] = Homework.objects.filter(
        teacher=teacher,
        status='active'
    ).count()

    # Pending / Partial Fee rows for IVR calls
    pending_fee_qs = (
        FeeCollection.objects.filter(status__in=['pending', 'partial'])
        .select_related('student', 'student__user', 'fee_structure')
        .order_by('-month')
    )

    pending_fee_rows = []
    for fc in pending_fee_qs:
        student = fc.student
        pending_fee_rows.append({
            'fee_collection_id': fc.id,
            'student_name': student.user.get_full_name() if student.user else str(student),
            'class_name': fc.fee_structure.class_name if fc.fee_structure else '',
            'father_phone': getattr(student, 'father_phone', '') or '',
            'mother_phone': getattr(student, 'mother_phone', '') or '',
            'amount_due': float(fc.amount_due),
            'amount_paid': float(fc.amount_paid),
            'pending_amount': float(fc.amount_due_balance),
            'fee_status': fc.status,
        })

    context['pending_fee_rows'] = pending_fee_rows

    # Weekly timetable for the teacher's assigned sections
    week_start = date.today() - timedelta(days=date.today().weekday())
    section_ids = teacher.subject_allocations.values_list('section_id', flat=True)
    context['timetable'] = Timetable.objects.filter(
        section_id__in=section_ids,
        week_start_date=week_start,
    ).select_related('subject', 'section').order_by('section__name', 'day', 'start_time')
    context['timetable_week_start'] = week_start

    return render(
        request,
        'dashboard/teacher_dashboard.html',
        context
    )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@login_required(login_url='accounts:login')
@role_required('student')
def student_dashboard(request):

    try:

        student = request.user.student_profile

    except Exception:

        return redirect('accounts:profile')

    context = {}

    context['student'] = student

    # Student age (template uses it)
    try:
        if student.dob:
            today = date.today()
            context['student_age'] = today.year - student.dob.year - (
                (today.month, today.day) < (student.dob.month, student.dob.day)
            )
        else:
            context['student_age'] = None
    except Exception:
        context['student_age'] = None


    # =====================================
    # Announcements for student dashboard
    # =====================================
    context['notices'] = Notice.objects.filter(
        is_active=True
    ).order_by('-created_at')[:5]

    # =====================================
    # Homework pending count
    # =====================================
    pending_homework_qs = Homework.objects.filter(
        status='active',
        section=student.section,
    )

    submitted_homework_ids = set(
        StudentSubmission.objects.filter(
            student=student,
            homework__in=pending_homework_qs,
        ).values_list('homework_id', flat=True)
    )

    context['pending_homework'] = pending_homework_qs.exclude(
        id__in=submitted_homework_ids
    ).count()

    # =====================================
    # Fees summary for student dashboard
    # =====================================
    today = date.today()

    fee_qs = FeeCollection.objects.filter(
        student=student,
        month__lte=today).order_by('-month')

    fee_status_obj = fee_qs.first()

    fee_structure_name = None
    fee_due = 0
    fee_paid = 0
    fee_balance = 0
    fee_month = None

    if fee_status_obj:

        fee_structure_name = (
            f"{fee_status_obj.fee_structure.class_name} - "
            f"{fee_status_obj.fee_structure.get_fee_type_display()}"
        )

        fee_due = float(fee_status_obj.amount_due)

        fee_paid = float(fee_status_obj.amount_paid)

        fee_balance = float(
            fee_status_obj.amount_due_balance
        )

        fee_month = fee_status_obj.month

        context['fee_structure_name'] = fee_structure_name
        context['fee_due'] = fee_due
        context['fee_paid'] = fee_paid
        context['fee_balance'] = fee_balance
        context['fee_month'] = fee_month

        # Always set latest fee status object so dashboard refresh shows latest payment.
        context['fee_status'] = fee_status_obj


    # =====================================
    # Timetable for student's section (current calendar week)
    # =====================================
    week_start = today - timedelta(days=today.weekday())
    context['timetable'] = Timetable.objects.filter(
        section=student.section,
        week_start_date=week_start,
    ).order_by('day', 'start_time')[:50]
    context['timetable_week_start'] = week_start


    total_attendance = StudentAttendance.objects.filter(
        student=student
    ).count()


    present_attendance = StudentAttendance.objects.filter(
        student=student,
        is_present=True
    ).count()

    attendance_percentage = 0

    if total_attendance > 0:

        attendance_percentage = (
            present_attendance / total_attendance
        ) * 100



    context['attendance_percentage'] = round(
        attendance_percentage,
        2
    )

    context['recent_marks'] = StudentMarks.objects.filter(
        student=student
    ).order_by('-created_at')[:5]

    context['report_cards'] = ReportCard.objects.filter(
        student=student
    ).order_by('-id')[:5]

    context['transport'] = StudentTransport.objects.filter(
        student=student,
        is_active=True
    ).first()

    context['hostel'] = HostelAllocation.objects.filter(
        student=student,
        is_active=True
    ).first()

    # =====================================
    # Exam timetable for student's section
    # =====================================
    context['exam_timetable'] = ExamSchedule.objects.filter(
        section=student.section,
    ).select_related('exam', 'subject', 'section').order_by('exam_date', 'start_time')[:100]


    # =====================================
    # Student month-wise attendance calendar
    # =====================================
    # Month is passed as YYYY-MM via ?month=YYYY-MM (optional)
    month_param = request.GET.get('month')
    try:
        if month_param:
            sel_year, sel_month = [int(x) for x in month_param.split('-')]
            selected_month_date = date(sel_year, sel_month, 1)
        else:
            selected_month_date = today.replace(day=1)
    except Exception:
        selected_month_date = today.replace(day=1)

    import calendar as _calendar

    first_day = selected_month_date
    last_day_num = _calendar.monthrange(first_day.year, first_day.month)[1]
    last_day = date(first_day.year, first_day.month, last_day_num)

    # Placeholder holidays: repository has no holiday model yet.
    # If you later add a Holiday table, replace this with real data.
    holidays_set = set()

    # Pull attendance for the month
    attendance_qs = StudentAttendance.objects.filter(
        student=student,
        date__gte=first_day,
        date__lte=last_day,
    ).only('date', 'is_present', 'remarks')

    attendance_by_date = {}
    for a in attendance_qs:
        status = 'absent'
        if a.is_present:
            # half-day heuristic from remarks
            if a.remarks and ('half' in a.remarks.lower()):
                status = 'half'
            else:
                status = 'present'
        else:
            # absent can also be marked as half; keep simple: if remarks has half => half
            if a.remarks and ('half' in a.remarks.lower()):
                status = 'half'
        attendance_by_date[a.date] = status

    # Build calendar grid starting on Monday
    start_weekday = first_day.weekday()  # Monday=0
    grid_start = first_day - timedelta(days=start_weekday)
    weeks = []
    current_day = grid_start

    # 6 weeks grid to cover all layouts
    for _ in range(6):
        week = []
        for _ in range(7):
            day_obj = current_day
            status = None
            is_holiday = day_obj in holidays_set
            in_month = (day_obj.month == first_day.month)

            if is_holiday:
                status = 'holiday'
            elif in_month and day_obj in attendance_by_date:
                status = attendance_by_date[day_obj]

            week.append({
                'date': day_obj,
                'day': day_obj.day,
                'in_month': in_month,
                'status': status,
            })

            current_day += timedelta(days=1)
        weeks.append(week)

    context['attendance_calendar'] = {
        'year': first_day.year,
        'month': first_day.month,
        'month_label': first_day.strftime('%B %Y'),
        'weeks': weeks,
        'prev_month': (first_day.replace(day=1) - timedelta(days=1)).strftime('%Y-%m'),
        'next_month': ((first_day.replace(day=1) + timedelta(days=32)).replace(day=1)).strftime('%Y-%m'),
        'holidays_enabled': False,
    }

    return render(
        request,
        'dashboard/student_dashboard.html',
        context
    )




# =========================================================
# ACCOUNTANT DASHBOARD
# =========================================================

@login_required(login_url='accounts:login')
@role_required('accountant')
def accountant_dashboard(request):

    context = {}

    today = date.today()

    month_start = today.replace(day=1)

    month_income = Income.objects.filter(
        date__gte=month_start
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    month_expense = Expense.objects.filter(
        date__gte=month_start
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    context['month_income'] = month_income

    context['month_expense'] = month_expense

    context['balance'] = (
        month_income - month_expense
    )

    return render(
        request,
        'dashboard/accountant_dashboard.html',
        context
    )


# =========================================================
# LIBRARIAN DASHBOARD
# =========================================================

@login_required(login_url='accounts:login')
@role_required('librarian')
def librarian_dashboard(request):

    context = {}

    context['total_books'] = Book.objects.count()

    context['issued_books'] = BookIssue.objects.filter(
        status='issued'
    ).count()

    return render(
        request,
        'dashboard/librarian_dashboard.html',
        context
    )


# =========================================================
# AJAX DASHBOARD DATA
# =========================================================

@login_required(login_url='accounts:login')
def dashboard_data(request):

    data = {}

    try:

        role = request.user.profile.role

        data['role'] = role

    except Exception:

        data['role'] = 'unknown'

    return JsonResponse(data)
def bus_students(request, bus_id):
    bus = Bus.objects.select_related(
        'driver',
        'teacher'
    ).get(id=bus_id)

    students = StudentTransport.objects.filter(
        bus=bus,
        is_active=True
    ).select_related(
        'student__user',
        'student__section'
    )

    context = {
        'bus': bus,
        'students': students
    }

    return render(
        request,
        'dashboard/bus_students.html',
        context
    )

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg
from datetime import date, timedelta
from apps.accounts.decorators import role_required

from apps.students.models import Student, StudentAttendance
from apps.teachers.models import (
    Teacher,
    TeacherAttendance,
    TeacherLeaveRequest
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
from apps.transport.models import StudentTransport
from apps.hostel.models import HostelAllocation
from apps.finance.models import (
    Income,
    Expense
)
from apps.noticeboard.models import (
    Notice,
    Event
)
from apps.timetable.models import Timetable

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

    total_students = Student.objects.filter(
        is_active=True
    ).count()

    attendance_percentage = 0

    if total_students > 0:

        attendance_percentage = (

            students_present / total_students

        ) * 100


    context['students_present'] = students_present

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

    teacher_attendance_percentage = 0

    if total_teachers > 0:

        teacher_attendance_percentage = (
            teacher_present_today / total_teachers
        ) * 100

    context['teacher_present_today'] = teacher_present_today

    context['teacher_attendance_percentage'] = round(
        teacher_attendance_percentage,
        2
    )

    return context


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

    # Section filter (template uses these)
    context['sections'] = Section.objects.all()
    context['selected_section'] = request.GET.get('section', '')

    # Optional template variables referenced in admin_dashboard.html
    context.setdefault('pending_fee_students', 0)
    context.setdefault('upcoming_birthdays', [])
    context.setdefault('top_pending_fees', [])

    return render(
        request,
        'dashboard/admin_dashboard.html',
        context
    )


# =========================================================
# PRINCIPAL DASHBOARD
# =========================================================

@login_required(login_url='accounts:login')
@role_required('principal')
def principal_dashboard(request):

    # Handle "Publish" announcement coming from principal dashboard.
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        priority = request.POST.get('priority', 'medium').strip()
        content = request.POST.get('content', '').strip()

        if title and content:
            Notice.objects.create(
                title=title,
                priority=priority if priority else 'medium',
                content=content,
                created_by=request.user,
                is_active=True,
            )

        # Redirect to avoid resubmission and to refresh notices for teacher dashboard.
        return redirect('dashboard:principal_dashboard')

    context = get_dashboard_context(request)

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
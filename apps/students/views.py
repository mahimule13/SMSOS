from datetime import date, timedelta
import calendar as _calendar

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from apps.accounts.decorators import admin_required, role_required
from apps.accounts.models import UserProfile
from .models import Student, StudentAttendance
from apps.classes.models import Section, ClassModel
from apps.fees.models import FeeStructure, FeeCollection
from apps.exams.models import StudentMarks, ReportCard
import uuid


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def student_list(request):
    section_id = request.GET.get('section')
    search_query = request.GET.get('search', '').strip()

    students = Student.objects.select_related('user', 'section', 'section__class_model').filter(is_active=True)

    if section_id:
        students = students.filter(section_id=section_id)

    if search_query:
        query = search_query.strip()
        students = students.filter(
            Q(student_id__iexact=query) |
            Q(admission_number__iexact=query) |
            Q(user__username__iexact=query) |
            Q(user__email__iexact=query) |
            Q(user__first_name__iexact=query) |
            Q(user__last_name__iexact=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    sections = Section.objects.filter(is_active=True)
    context = {
        'students': students,
        'sections': sections,
        'selected_section': section_id,
        'search_query': search_query,
    }
    return render(request, 'students/list.html', context)


@login_required(login_url='accounts:login')
@role_required('super_admin', 'school_admin', 'principal')
def create_student(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email') or f"{phone}@sms.local"

        username_in = (request.POST.get('username') or '').strip()
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Password validation
        if password != password2:
            messages.error(request, 'Password and Confirm Password do not match')
        else:
            # Base username (optional override)
            username = username_in or phone or f"student{Student.objects.count() + 1001}"

            # Username uniqueness
            if User.objects.filter(username=username).exists():
                if username_in:
                    messages.error(request, 'Username already exists. Please choose another username.')
                    return redirect('students:create')

                # Auto-generate a free username
                username = f"student{Student.objects.count() + 1001}"
                while User.objects.filter(username=username).exists():
                    username = f"student{Student.objects.count() + 1001 + int(uuid.uuid4().int % 1000)}"

            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                )

                section = Section.objects.get(id=request.POST.get('section'))

                fee_structure = None
                fee_structure_id = request.POST.get('fee_structure')
                if fee_structure_id:
                    fee_structure = FeeStructure.objects.filter(id=fee_structure_id).first()

                student = Student.objects.create(
                    user=user,
                    student_id=f"STU{Student.objects.count() + 1001}",
                    admission_number=request.POST.get('admission_number'),
                    roll_number=request.POST.get('roll_number'),
                    dob=request.POST.get('dob'),
                    gender=request.POST.get('gender', 'M'),
                    blood_group=request.POST.get('blood_group', ''),
                    address=request.POST.get('address', ''),
                    phone=phone,
                    email=email,
                    photo=request.FILES.get('photo'),
                    section=section,
                    father_name=request.POST.get('father_name', ''),
                    father_phone=request.POST.get('father_phone', ''),
                    mother_name=request.POST.get('mother_name', ''),
                    mother_phone=request.POST.get('mother_phone', ''),
                    guardian_name=request.POST.get('guardian_name', ''),
                    guardian_phone=request.POST.get('guardian_phone', ''),
                    admission_date=request.POST.get('admission_date'),
                )

                UserProfile.objects.create(
                    user=user,
                    role='student',
                    school_id=request.user.profile.school_id,
                    school_name=request.user.profile.school_name,
                    phone=phone,
                    address=request.POST.get('address', ''),
                    gender=request.POST.get('gender', 'M'),
                    dob=request.POST.get('dob'),
                    photo=request.FILES.get('photo'),
                )

                if fee_structure:
                    FeeCollection.objects.create(
                        student=student,
                        fee_structure=fee_structure,
                        month=date.today().replace(day=1),
                        amount_due=fee_structure.amount,
                        amount_paid=0,
                        status='pending'
                    )

                messages.success(request, 'Student created successfully')
                return redirect('students:list')
            except Exception as e:
                messages.error(request, str(e))

    classes = ClassModel.objects.filter(is_active=True)
    sections = Section.objects.filter(is_active=True)
    fee_structures = FeeStructure.objects.filter(is_active=True)
    context = {'classes': classes, 'sections': sections, 'fee_structures': fee_structures}
    return render(request, 'students/create.html', context)


def build_attendance_calendar(student, month_str=None):
    """
    Build a calendar grid showing attendance for the given student for a selected month.
    month_str format: 'YYYY-MM' or None for current month.
    """
    try:
        if month_str:
            year, month = [int(x) for x in month_str.split('-')]
            selected_month_date = date(year, month, 1)
        else:
            selected_month_date = date.today().replace(day=1)
    except Exception:
        selected_month_date = date.today().replace(day=1)

    first_day = selected_month_date
    last_day_num = _calendar.monthrange(first_day.year, first_day.month)[1]
    last_day = date(first_day.year, first_day.month, last_day_num)

    # Placeholder holidays (no holiday model)
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
            if a.remarks and ('half' in a.remarks.lower()):
                status = 'half'
            else:
                status = 'present'
        else:
            if a.remarks and ('half' in a.remarks.lower()):
                status = 'half'
        attendance_by_date[a.date] = status

    # Build calendar grid starting on Monday
    start_weekday = first_day.weekday()  # Monday=0
    grid_start = first_day - timedelta(days=start_weekday)
    weeks = []
    current_day = grid_start

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

    return {
        'year': first_day.year,
        'month': first_day.month,
        'month_label': first_day.strftime('%B %Y'),
        'weeks': weeks,
        'prev_month': (first_day.replace(day=1) - timedelta(days=1)).strftime('%Y-%m'),
        'next_month': ((first_day.replace(day=1) + timedelta(days=32)).replace(day=1)).strftime('%Y-%m'),
        'holidays_enabled': False,
    }


@login_required(login_url='accounts:login')
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    today = date.today()

    marks = StudentMarks.objects.filter(
        student=student
    ).select_related('exam', 'subject').order_by('-exam__start_date', 'subject__name')

    report_cards = ReportCard.objects.filter(
        student=student
    ).order_by('-exam__start_date')

    # Attendance calendar
    month_param = request.GET.get('month')
    attendance_calendar = build_attendance_calendar(student, month_param)

    context = {
        'student': student,
        'marks': marks,
        'report_cards': report_cards,
        'attendance_calendar': attendance_calendar,
    }
    return render(request, 'students/detail.html', context)


@login_required(login_url='accounts:login')
@role_required('super_admin', 'school_admin', 'principal')
def edit_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        student.user.first_name = request.POST.get('first_name')
        student.user.last_name = request.POST.get('last_name')
        student.user.save()
        
        student.phone = request.POST.get('phone')
        student.address = request.POST.get('address')
        student.father_name = request.POST.get('father_name')
        student.mother_name = request.POST.get('mother_name')
        student.save()
        
        messages.success(request, 'Student updated successfully')
        return redirect('students:list')
    
    context = {'student': student}
    return render(request, 'students/edit.html', context)


@login_required(login_url='accounts:login')
@role_required('super_admin', 'school_admin', 'principal')
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.user.delete()
    messages.success(request, 'Student deleted successfully')
    return redirect('students:list')


@login_required(login_url='accounts:login')
@role_required('super_admin', 'school_admin', 'principal', 'teacher')
def attendance_view(request):
    today = date.today()
    attendance_date = request.GET.get('date') or today.isoformat()
    section_id = request.GET.get('section')

    
    students = Student.objects.filter(is_active=True)
    sections = Section.objects.all()

    if request.user.profile.role == 'teacher':
        teacher = request.user.teacher_profile
        allowed_sections = teacher.subject_allocation.values_list('section', flat=True).distinct()
        students = students.filter(section__in=allowed_sections)
        sections = Section.objects.filter(id__in=allowed_sections)

    if section_id:
        students = students.filter(section_id=section_id)
    
    if request.method == 'POST':
        post_date = request.POST.get('date') or today.isoformat()
        for student in students:
            is_present = request.POST.get(f'present_{student.id}') == 'on'
            StudentAttendance.objects.update_or_create(
                student=student,
                date=post_date,
                defaults={'is_present': is_present, 'marked_by': request.user.teacher_profile if hasattr(request.user, 'teacher_profile') else None}
            )

        
        messages.success(request, 'Attendance marked successfully')
    
    context = {
        'students': students,
        'date': attendance_date,
        'sections': sections,
        'selected_section': section_id,
    }

    return render(request, 'students/attendance.html', context)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.homework.models import Assignment, AssignmentSubmission


@login_required(login_url='login')
def student_assignments(request):
    try:
        student = request.user.student_profile
    except Exception:
        messages.error(request, 'Your student profile is not set up yet. Contact the principal/admin to create it.')
        return redirect('accounts:profile')

    assignments = (
        Assignment.objects.filter(section=student.section)
        .select_related('subject', 'section')
        .order_by('-created_at')
    )

    submitted_assignment_ids = set(
        AssignmentSubmission.objects.filter(student=student, assignment__in=assignments)
        .values_list('assignment_id', flat=True)
    )

    context = {
        'assignments': assignments,
        'submitted_assignment_ids': submitted_assignment_ids,
    }

    return render(request, 'students/assignments.html', context)


@login_required(login_url='login')
def submit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)

    try:
        student = request.user.student_profile
    except Exception:
        messages.error(request, 'Your student profile is not set up yet. Contact the principal/admin to create it.')
        return redirect('accounts:profile')

    if assignment.section_id != student.section_id:
        messages.error(request, 'This assignment is not assigned to your section.')
        return redirect('students:student_assignments')

    if request.method == 'POST':
        if 'submission_file' not in request.FILES:
            messages.error(request, 'Please upload your assignment file.')
            return redirect('students:submit_assignment', pk=pk)

        AssignmentSubmission.objects.update_or_create(
            assignment=assignment,
            student=student,
            defaults={'submission_file': request.FILES['submission_file']}
        )

        messages.success(request, 'Assignment submitted successfully.')
        return redirect('students:my_submissions')

    context = {'assignment': assignment}
    return render(request, 'students/submit_assignment.html', context)


@login_required(login_url='login')
def my_submissions(request):
    student = request.user.student_profile

    submissions = (
        AssignmentSubmission.objects.filter(student=student)
        .select_related('assignment', 'assignment__subject', 'assignment__section')
        .order_by('-submitted_at')
    )

    context = {'submissions': submissions}
    return render(request, 'students/my_submissions.html', context)


@login_required(login_url='login')
def assignment_submission_detail(request, pk):
    student = request.user.student_profile
    submission = get_object_or_404(AssignmentSubmission, pk=pk, student=student)

    context = {'submission': submission}
    return render(request, 'students/submission_detail.html', context)

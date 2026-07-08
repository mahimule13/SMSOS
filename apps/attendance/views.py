from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta , datetime

from apps.classes.models import ClassModel, Section
from urllib3 import request
from apps.accounts.decorators import role_required
from apps.accounts.models import UserProfile
from apps.teachers.models import Teacher, TeacherAttendance
from apps.students.models import Student, StudentAttendance
from .models import PrincipalAttendance
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table
from django.db.models import Count
from django.db.models.functions import TruncDate
import json


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'teacher', 'principal')
def attendance_dashboard(request):
    teachers = Teacher.objects.filter(is_active=True)
    principals = UserProfile.objects.filter(role='principal')
    today = timezone.now().date()

    if request.method == 'POST':
        attendance_date = request.POST.get('date') or today
        attendance_role = request.POST.get('role')
        attendance_mode = request.POST.get('attendance_mode')

        # Backward/compat: if mode is provided, override role.
        if attendance_mode in ['teacher', 'student']:
            attendance_role = attendance_mode
        person_id = request.POST.get('person')

        user_role = request.user.profile.role

        if attendance_role == 'teacher':
            # Only teachers/admins can mark teacher attendance
            if user_role not in ['super_admin', 'school_admin', 'teacher']:
                messages.error(request, 'Access denied for marking teacher attendance.')
                return redirect('attendance:dashboard')

            teacher = get_object_or_404(Teacher, pk=person_id)
            TeacherAttendance.objects.update_or_create(
                teacher=teacher,
                date=attendance_date,
                defaults={'is_present': True, 'marked_by': request.user}
            )
            messages.success(request, f"Attendance marked for teacher {teacher.user.get_full_name()}.")

        elif attendance_role == 'principal':
            # Only principals/admins can mark principal attendance
            if user_role not in ['super_admin', 'school_admin', 'principal']:
                messages.error(request, 'Access denied for marking principal attendance.')
                return redirect('attendance:dashboard')

            principal_profile = get_object_or_404(UserProfile, pk=person_id, role='principal')
            PrincipalAttendance.objects.update_or_create(
                principal=principal_profile.user,
                date=attendance_date,
                defaults={'is_present': True, 'marked_by': request.user}
            )
            messages.success(request, f"Attendance marked for principal {principal_profile.user.get_full_name()}.")

        elif attendance_role == 'student':
            # Allow staff to mark student attendance.
            # If you want ONLY principals, change this back to `user_role != 'principal'`.
            if user_role not in ['super_admin', 'school_admin', 'principal', 'teacher']:
                messages.error(request, 'Access denied for marking student attendance.')
                return redirect('attendance:dashboard')

            student = get_object_or_404(Student, pk=person_id)
            StudentAttendance.objects.update_or_create(
                student=student,
                date=attendance_date,
                defaults={'is_present': True, 'marked_by': request.user.teacher_profile if hasattr(request.user, 'teacher_profile') else None}
            )

            messages.success(request, f"Attendance marked for student {student.user.get_full_name()}.")


        else:
            messages.error(request, 'Please select a valid attendance role.')


        # After marking, take the user back to Student Attendance UI.
        return redirect('students:attendance')

    teacher_present_today = TeacherAttendance.objects.filter(date=today, is_present=True).count()

    principal_present_today = PrincipalAttendance.objects.filter(date=today, is_present=True).count()
    student_present_today = StudentAttendance.objects.filter(date=today, is_present=True).count()

    context = {
        'teachers': teachers,
        'principals': principals,
        'students': Student.objects.filter(is_active=True),
        'today': today,
        'teacher_present_today': teacher_present_today,
        'principal_present_today': principal_present_today,
        'student_present_today': student_present_today,
        'total_teachers': teachers.count(),
        'total_principals': principals.count(),
        'total_students': Student.objects.filter(is_active=True).count(),
    }
    return render(request, 'attendance/dashboard.html', context)
@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal', 'teacher')
def teacher_attendance(request):
    """Separate entry point for marking teacher attendance."""
    return redirect('teachers:attendance')


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal', 'teacher')
def student_attendance(request):
    """Separate entry point for marking student attendance."""
    return redirect('students:attendance')
@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def attendance_reports(request):
    student_id = request.GET.get('student_id')
    print("Student ID =", student_id)
    section_id = request.GET.get('section')

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    today = timezone.now().date()
    selected_section = request.GET.get('section')

    students = Student.objects.filter(is_active=True)

    if selected_section:
        students = students.filter(
            section_id=selected_section
        )
    week_start = today - timedelta(days=7)
    month_start = today.replace(day=1)
    if from_date:
        week_start = datetime.strptime(from_date, "%Y-%m-%d").date()
    else:
        week_start = today - timedelta(days=7)

    if from_date:
        month_start = datetime.strptime(from_date, "%Y-%m-%d").date().replace(day=1)
    else:
        month_start = today.replace(day=1)
    # Daily
    teacher_daily_present = TeacherAttendance.objects.filter(
        date=today,
        is_present=True
    ).count()

    student_daily_present = StudentAttendance.objects.filter(
        student__in=students,
        date=today,
        is_present=True
    ).count()

    teacher_daily_absent = TeacherAttendance.objects.filter(
        date=today,
        is_present=False
    ).count()

    student_daily_absent = StudentAttendance.objects.filter(
        student__in=students,
        date=today,
        is_present=False
    ).count()

    # Weekly
    teacher_weekly = TeacherAttendance.objects.filter(
        date__gte=week_start,
        is_present=True
    ).count()

    student_weekly = StudentAttendance.objects.filter(
        student__in=students,
        date__gte=week_start,
        is_present=True
    ).count()

    # Monthly
    teacher_monthly = TeacherAttendance.objects.filter(
        date__gte=month_start,
        is_present=True
    ).count()

    student_monthly = StudentAttendance.objects.filter(
        student__in=students,
        date__gte=month_start,
        is_present=True
    ).count()

    # Totals
    total_teacher_records = TeacherAttendance.objects.count()
    total_student_records = StudentAttendance.objects.count()

    teacher_percentage = round(
        (TeacherAttendance.objects.filter(is_present=True).count() * 100)
        / total_teacher_records,
        2
    ) if total_teacher_records else 0

    student_percentage = round(
        (StudentAttendance.objects.filter(is_present=True).count() * 100)
        / total_student_records,
        2
    ) if total_student_records else 0

    # Recent records
    teacher_records = TeacherAttendance.objects.select_related(
        'teacher__user'
    ).order_by('-date')[:20]
    student_records = StudentAttendance.objects.select_related(
    'student__user',
    'student__section__class_model'
    ).order_by('-date')
    # ==========================================
    # STUDENT CHART DATA
    # ==========================================

    daily_students = (
        StudentAttendance.objects
        .filter(date=today)
        .values('date')
        .annotate(total=Count('id'))
    )

    weekly_students = StudentAttendance.objects.filter(
        student__in=students
    )

    if from_date:
        weekly_students = weekly_students.filter(date__gte=from_date)

    if to_date:
        weekly_students = weekly_students.filter(date__lte=to_date)

    weekly_students = (
        weekly_students
        .values('date')
        .annotate(total=Count('id'))
        .order_by('date')
    )

    monthly_students = StudentAttendance.objects.filter(
        student__in=students
    )

    if from_date:
        monthly_students = monthly_students.filter(date__gte=from_date)

    if to_date:
        monthly_students = monthly_students.filter(date__lte=to_date)

    monthly_students = (
        monthly_students
        .values('date')
        .annotate(total=Count('id'))
        .order_by('date')
    )

    student_labels = [
        str(item['date'])
        for item in monthly_students
    ]

    student_daily_data = [
        student_daily_present
        for _ in student_labels
    ]

    student_weekly_data = [
        item['total']
        for item in weekly_students
    ]

    student_monthly_data = [
        item['total']
        for item in monthly_students
    ]

# ==========================================
# TEACHER CHART DATA
# ==========================================

    
    weekly_teachers = TeacherAttendance.objects.all()

    if from_date:
        weekly_teachers = weekly_teachers.filter(date__gte=from_date)

    if to_date:
        weekly_teachers = weekly_teachers.filter(date__lte=to_date)

    weekly_teachers = (
        weekly_teachers
        .values('date')
        .annotate(total=Count('id'))
        .order_by('date')
    )

    monthly_teachers = TeacherAttendance.objects.all()

    if from_date:
        monthly_teachers = monthly_teachers.filter(date__gte=from_date)

    if to_date:
        monthly_teachers = monthly_teachers.filter(date__lte=to_date)

    monthly_teachers = (
        monthly_teachers
        .values('date')
        .annotate(total=Count('id'))
        .order_by('date')
    )
    teacher_labels = [
        str(item['date'])
        for item in monthly_teachers
    ]

    teacher_daily_data = [
        teacher_daily_present
        for _ in teacher_labels
    ]

    teacher_weekly_data = [
        item['total']
        for item in weekly_teachers
    ]

    teacher_monthly_data = [
        item['total']   
        for item in monthly_teachers
    ]
    # ==========================================
    # STUDENT REPORT FILTER
    # ==========================================

    student_attendance_qs = StudentAttendance.objects.select_related(
        'student__user',
        'student__section__class_model'
        )

    if student_id:
        student_attendance_qs = student_attendance_qs.filter(
            student__student_id__icontains=student_id
            )

    if section_id:
        student_attendance_qs = student_attendance_qs.filter(
            student__section_id=section_id
            )

    if from_date:
        student_attendance_qs = student_attendance_qs.filter(
            date__gte=from_date
            )

    if to_date:
        student_attendance_qs = student_attendance_qs.filter(
            date__lte=to_date
        )
    print("Filtered Count =", student_attendance_qs.count())

    for i in student_attendance_qs:
        print(i.student.student_id, i.date, i.is_present)
    student_report_records = student_attendance_qs.order_by('-date')

    student_total = student_attendance_qs.count()

    student_present = student_attendance_qs.filter(
        is_present=True
        ).count()

    student_absent = student_attendance_qs.filter(
        is_present=False
        ).count()

    student_percentage_report = round(
        (student_present * 100) / student_total,
        2) if student_total else 0

    student_weekly_report = student_attendance_qs.filter(
        date__gte=week_start,
        is_present=True
        ).count()

    student_monthly_report = student_attendance_qs.filter(
        date__gte=month_start,
        is_present=True
    ).count()

    student_report_records = student_attendance_qs.order_by('-date')
    print("Student Labels:", student_labels)
    print("Student Weekly:", student_weekly_data)
    print("Student Monthly:", student_monthly_data)
    print("Teacher Labels:", teacher_labels)
    print("Teacher Weekly:", teacher_weekly_data)
    print("Teacher Monthly:", teacher_monthly_data)
    print("student_weekly_data =", student_weekly_data)
    print("student_monthly_data =", student_monthly_data)

    print("teacher_weekly_data =", teacher_weekly_data)
    print("teacher_monthly_data =", teacher_monthly_data)
    context = {

    # Daily
    'teacher_present': teacher_daily_present,
    'teacher_absent': teacher_daily_absent,

    'student_present': student_daily_present,
    'student_absent': student_daily_absent,

    # Weekly
    'weekly_teacher': teacher_weekly,
    'weekly_student': student_weekly,

    # Monthly
    'monthly_teacher': teacher_monthly,
    'monthly_student': student_monthly,

    # Percentage
    'teacher_percentage': teacher_percentage,
    'student_percentage': student_percentage,

    # Tables
    'teacher_records': teacher_records,
    'student_records': student_report_records,

    # Charts
    'student_labels': json.dumps(student_labels),
    'student_daily_data': json.dumps(student_daily_data),
    'student_weekly_data': json.dumps(student_weekly_data),
    'student_monthly_data': json.dumps(student_monthly_data),
    'teacher_labels': json.dumps(teacher_labels),
    'teacher_daily_data': json.dumps(teacher_daily_data),
    'teacher_weekly_data': json.dumps(teacher_weekly_data),
    'teacher_monthly_data': json.dumps(teacher_monthly_data),
    'sections' : Section.objects.filter(is_active=True),
    'selected_section' : selected_section,
    'student_total': student_total,
    'student_present_report': student_present,
    'student_absent_report': student_absent,
    'student_percentage_report': student_percentage_report,
    'student_weekly_report': student_weekly_report,
    'student_monthly_report': student_monthly_report,
    'student_id': student_id,
    'from_date': from_date,
    'to_date': to_date,
    'class_attendance': [],
}
    print("student_labels =", student_labels)
    print("teacher_labels =", teacher_labels)
    return render(
        request,
        'attendance/reports.html',
        context
    )
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def export_excel(request):

    wb = Workbook()
    ws = wb.active

    ws.append([
        'Student',
        'Date',
        'Status'
    ])

    records = StudentAttendance.objects.select_related(
        'student__user'
    )

    for record in records:

        ws.append([
            record.student.user.get_full_name(),
            str(record.date),
            'Present' if record.is_present else 'Absent'
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response['Content-Disposition'] = (
        'attachment; filename=attendance.xlsx'
    )

    wb.save(response)

    return response


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def export_pdf(request):

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        'attachment; filename=attendance.pdf'
    )

    doc = SimpleDocTemplate(response)

    data = [
        ['Student', 'Date', 'Status']
    ]

    records = StudentAttendance.objects.select_related(
        'student__user'
    )

    for record in records:

        data.append([
            record.student.user.get_full_name(),
            str(record.date),
            'Present' if record.is_present else 'Absent'
        ])

    table = Table(data)

    doc.build([table])

    return response
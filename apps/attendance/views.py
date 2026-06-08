from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.accounts.decorators import role_required
from apps.accounts.models import UserProfile
from apps.teachers.models import Teacher, TeacherAttendance
from apps.students.models import Student, StudentAttendance
from .models import PrincipalAttendance



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
@role_required('super_admin', 'school_admin', 'teacher', 'principal')
def attendance_reports(request):
    context = {}
    return render(request, 'attendance/reports.html', context)


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


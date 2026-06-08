from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from apps.accounts.decorators import admin_required, role_required
from apps.accounts.models import UserProfile
from apps.classes.models import Subject
from .models import Teacher, TeacherAttendance, TeacherLeaveRequest


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def teacher_list(request):
    teachers = Teacher.objects.all()
    context = {'teachers': teachers}
    return render(request, 'teachers/list.html', context)


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def create_teacher(request):
    subjects = Subject.objects.all()
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username') or (email.split('@')[0] if email else None)
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        employee_id = request.POST.get('employee_id')
        specialization_id = request.POST.get('specialization')
        specialization = Subject.objects.filter(id=specialization_id).first() if specialization_id else None

        if password and password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'teachers/create.html', {'subjects': subjects})

        if not username:
            messages.error(request, 'Username is required')
            return render(request, 'teachers/create.html', {'subjects': subjects})

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'teachers/create.html', {'subjects': subjects})

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )

            if password:
                user.set_password(password)
                user.save()

            teacher = Teacher.objects.create(
                user=user,
                login_username=username,
                login_password=make_password(password) if password else '',
                employee_id=employee_id,
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
                gender=request.POST.get('gender', 'M'),
                blood_group=request.POST.get('blood_group', ''),
                dob=request.POST.get('dob'),
                photo=request.FILES.get('photo'),
                aadhar=request.POST.get('aadhar', ''),
                pan=request.POST.get('pan', ''),
                qualification=request.POST.get('qualification', ''),
                specialization=specialization,
                experience_years=request.POST.get('experience_years', 0),
                joining_date=request.POST.get('joining_date'),
                base_salary=request.POST.get('base_salary', 0),
            )

            UserProfile.objects.create(
                user=user,
                role='teacher',
                school_id=request.user.profile.school_id,
                school_name=request.user.profile.school_name,
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
                gender=request.POST.get('gender', 'M'),
                dob=request.POST.get('dob'),
                photo=request.FILES.get('photo')
            )
            messages.success(request, 'Teacher created successfully')
            return redirect('teachers:list')
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'teachers/create.html', {'subjects': subjects})


@login_required(login_url='login')
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    context = {'teacher': teacher}
    return render(request, 'teachers/detail.html', context)


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def edit_teacher(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    subjects = Subject.objects.all()
    blood_groups = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
    
    if request.method == 'POST':
        new_username = request.POST.get('username')
        if new_username and User.objects.filter(username=new_username).exclude(pk=teacher.user.pk).exists():
            messages.error(request, 'Username already taken')
            return redirect('teachers:edit', pk=pk)

        teacher.user.username = new_username or teacher.user.username
        teacher.login_username = new_username or teacher.login_username
        teacher.user.first_name = request.POST.get('first_name')
        teacher.user.last_name = request.POST.get('last_name')
        teacher.user.email = request.POST.get('email')

        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if new_password:
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match')
                return redirect('teachers:edit', pk=pk)
            teacher.user.set_password(new_password)
            teacher.login_password = make_password(new_password)

        teacher.user.save()
        
        teacher.phone = request.POST.get('phone')
        teacher.address = request.POST.get('address')
        teacher.gender = request.POST.get('gender')
        teacher.blood_group = request.POST.get('blood_group', '')
        teacher.dob = request.POST.get('dob')
        if request.FILES.get('photo'):
            teacher.photo = request.FILES.get('photo')
        teacher.aadhar = request.POST.get('aadhar', '')
        teacher.pan = request.POST.get('pan', '')
        teacher.qualification = request.POST.get('qualification')
        specialization_id = request.POST.get('specialization')
        teacher.specialization = Subject.objects.filter(id=specialization_id).first() if specialization_id else None
        teacher.experience_years = request.POST.get('experience_years')
        teacher.joining_date = request.POST.get('joining_date')
        teacher.base_salary = request.POST.get('base_salary')
        teacher.save()
        
        messages.success(request, 'Teacher updated successfully')
        return redirect('teachers:list')
    
    context = {'teacher': teacher, 'subjects': subjects, 'blood_groups': blood_groups}
    return render(request, 'teachers/edit.html', context)


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def delete_teacher(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    teacher.user.delete()
    messages.success(request, 'Teacher deleted successfully')
    return redirect('teachers:list')


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def teacher_attendance(request):
    attendance_date = request.GET.get('date')
    if request.method == 'POST':
        attendance_date = request.POST.get('date') or date.today().isoformat()
        teachers = Teacher.objects.filter(is_active=True)
        
        for teacher in teachers:
            is_present = request.POST.get(f'present_{teacher.id}') == 'on'
            TeacherAttendance.objects.update_or_create(
                teacher=teacher,
                date=attendance_date,
                defaults={'is_present': is_present, 'marked_by': request.user}
            )
        
        messages.success(request, 'Attendance marked successfully')
    
    teachers = Teacher.objects.filter(is_active=True)
    context = {'teachers': teachers, 'date': attendance_date or date.today().isoformat()}
    return render(request, 'teachers/attendance.html', context)


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def leave_requests(request):
    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')
        leave = get_object_or_404(TeacherLeaveRequest, pk=leave_id)

        if action == 'approve':
            leave.status = 'approved'
            leave.approved_by = request.user
            leave.remarks = request.POST.get('remarks', leave.remarks)
            leave.save()
            messages.success(request, 'Leave request approved successfully.')
        elif action == 'reject':
            leave.status = 'rejected'
            leave.approved_by = request.user
            leave.remarks = request.POST.get('remarks', leave.remarks)
            leave.save()
            messages.success(request, 'Leave request rejected successfully.')
        return redirect('teachers:leave_requests')

    leaves = TeacherLeaveRequest.objects.select_related('teacher__user').all()
    context = {'leaves': leaves}
    return render(request, 'teachers/leave_requests.html', context)

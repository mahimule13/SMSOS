from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from apps.accounts.decorators import admin_required, role_required
from apps.accounts.models import UserProfile
from .models import Student, StudentAttendance
from apps.classes.models import Section, ClassModel
from apps.fees.models import FeeStructure, FeeCollection
import uuid


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def student_list(request):
    section_id = request.GET.get('section')
    students = Student.objects.all()
    
    if section_id:
        students = students.filter(section_id=section_id)
    
    sections = Section.objects.all()
    context = {'students': students, 'sections': sections}
    return render(request, 'students/list.html', context)


@login_required(login_url='login')
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
    sections = Section.objects.all()
    fee_structures = FeeStructure.objects.filter(is_active=True)
    context = {'classes': classes, 'sections': sections, 'fee_structures': fee_structures}
    return render(request, 'students/create.html', context)


@login_required(login_url='login')
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    context = {'student': student}
    return render(request, 'students/detail.html', context)


@login_required(login_url='login')
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


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.user.delete()
    messages.success(request, 'Student deleted successfully')
    return redirect('students:list')


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal', 'teacher')
def attendance_view(request):
    today = date.today()
    attendance_date = request.GET.get('date') or today.isoformat()
    section_id = request.GET.get('section')

    
    students = Student.objects.filter(is_active=True)
    sections = Section.objects.all()

    if request.user.profile.role == 'teacher':
        teacher = request.user.teacher_profile
        allowed_sections = [sa.section for sa in teacher.subject_allocations.all()]
        students = students.filter(section__in=allowed_sections)
        sections = allowed_sections

    if section_id:
        students = students.filter(section_id=section_id)
    
    if request.method == 'POST':
        post_date = request.POST.get('date') or today.isoformat()
        for student in students:
            is_present = request.POST.get(f'present_{student.id}') == 'on'
            StudentAttendance.objects.update_or_create(
                student=student,
                date=attendance_date,
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

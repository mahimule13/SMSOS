from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import role_required
from .models import Homework, StudentSubmission
from apps.classes.models import Section


@login_required(login_url='login')
def homework_list(request):
    if request.user.profile.role == 'teacher':
        teacher = request.user.teacher_profile
        homework = Homework.objects.filter(teacher=teacher).order_by('-due_date')
        view_role = 'teacher'
    elif request.user.profile.role == 'student':
        try:
            student = request.user.student_profile
        except Exception:
            messages.error(
                request,
                'Your student profile is not set up yet. Contact the principal/admin to create it.'
            )
            return redirect('accounts:profile')

        homework = Homework.objects.filter(
            status='active',
            section=student.section
        ).order_by('-due_date')
        submitted_homework_ids = set(
            StudentSubmission.objects.filter(student=student, homework__in=homework)
            .values_list('homework_id', flat=True)
        )
        view_role = 'student'
    else:
        return redirect('dashboard:teacher_dashboard')

    context = {
        'homework': homework,
        'view_role': view_role,
        'submitted_homework_ids': submitted_homework_ids if request.user.profile.role == 'student' else set(),
    }
    return render(request, 'homework/list.html', context)


@login_required(login_url='login')
@role_required('teacher')
def create_homework(request):
    teacher = request.user.teacher_profile
    allocations = teacher.subject_allocations.select_related('section', 'subject')
    section_ids = []
    subject_ids = []
    sections = []
    subjects = []

    for alloc in allocations:
        if alloc.section_id not in section_ids:
            section_ids.append(alloc.section_id)
            sections.append(alloc.section)
        if alloc.subject_id not in subject_ids:
            subject_ids.append(alloc.subject_id)
            subjects.append(alloc.subject)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        section_id = request.POST.get('section')
        subject_id = request.POST.get('subject')
        due_date = request.POST.get('due_date')
        attachment = request.FILES.get('attachment')
        
        homework = Homework.objects.create(
            section_id=section_id,
            subject_id=subject_id,
            teacher=teacher,
            title=title,
            description=description,
            due_date=due_date,
            attachment=attachment
        )
        
        messages.success(request, 'Homework created successfully')
        return redirect('homework:list')
    
    context = {
        'sections': sections,
        'subjects': subjects,
    }
    return render(request, 'homework/create.html', context)


@login_required(login_url='login')
def homework_detail(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    submissions = StudentSubmission.objects.filter(homework=homework)
    context = {'homework': homework, 'submissions': submissions}
    return render(request, 'homework/detail.html', context)


@login_required(login_url='login')
@role_required('student')
def submit_homework(request, pk):
    homework = get_object_or_404(Homework, pk=pk)
    student = request.user.student_profile
    
    if request.method == 'POST':
        submission_file = request.FILES.get('submission_file')
        
        StudentSubmission.objects.update_or_create(
            homework=homework,
            student=student,
            defaults={'submission_file': submission_file}
        )
        
        messages.success(request, 'Homework submitted successfully')
        return redirect('homework:list')
    
    context = {'homework': homework}
    return render(request, 'homework/submit.html', context)

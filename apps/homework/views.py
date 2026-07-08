from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import role_required
from .models import Homework, StudentSubmission, Assignment, AssignmentSubmission
from apps.classes.models import Section, Subject


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

        Homework.objects.create(
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


@login_required
@role_required('teacher')
def create_assignment(request):

    if request.method == 'POST':
        Assignment.objects.create(
            title=request.POST.get('title'),
            subject_id=request.POST.get('subject'),
            section_id=request.POST.get('section'),
            description=request.POST.get('description'),
            total_marks=request.POST.get('total_marks'),
            due_date=request.POST.get('due_date'),
            created_by=request.user.teacher_profile
        )

        messages.success(request, 'Assignment created successfully.')
        return redirect('homework:assignment_list')

    context = {
        'subjects': Subject.objects.all(),
        'sections': Section.objects.filter(is_active=True),
    }

    return render(request, 'homework/assignment_create.html', context)


@login_required
@role_required('teacher')
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    context = {
        'assignment': assignment,
        'today': date.today(),
    }
    return render(request, 'homework/assignment_details.html', context)


@login_required
@role_required('teacher')
def edit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)

    if request.method == 'POST':
        assignment.title = request.POST.get('title')
        assignment.description = request.POST.get('description')
        assignment.total_marks = request.POST.get('total_marks')
        assignment.due_date = request.POST.get('due_date')
        assignment.subject_id = request.POST.get('subject')
        assignment.section_id = request.POST.get('section')
        assignment.save()

        messages.success(request, 'Assignment updated successfully.')
        return redirect('homework:assignment_list')

    return render(
        request,
        'homework/edit_assignment.html',
        {
            'assignment': assignment,
            'subjects': Subject.objects.all(),
            'sections': Section.objects.all(),
        }
    )


@login_required
@role_required('teacher')
def delete_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    assignment.delete()

    messages.success(request, 'Assignment deleted successfully.')
    return redirect('homework:assignment_list')


@login_required
@role_required('teacher')
def assignment_submissions(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    submissions = AssignmentSubmission.objects.filter(assignment=assignment).select_related('student', 'student__user').order_by('-submitted_at')

    context = {
        'assignment': assignment,
        'submissions': submissions
    }

    return render(request, 'homework/assignment_submissions.html', context)


@login_required(login_url='login')
def assignment_list(request):
    search_query = request.GET.get('search', '').strip()
    section_id = request.GET.get('section')

    assignments = (
        Assignment.objects
        .select_related('created_by', 'subject', 'section')
        .order_by('-created_at')
    )

    if search_query:
        assignments = assignments.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(subject__name__icontains=search_query)
        )

    if section_id:
        assignments = assignments.filter(section_id=section_id)

    context = {
        'assignments': assignments,
        'subjects': Subject.objects.all(),
        'sections': Section.objects.filter(is_active=True),
        'today': date.today(),
    }

    return render(request, 'homework/assignment_list.html', context)


@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(AssignmentSubmission, pk=pk)

    context = {
        'submission': submission
    }

    return render(request, 'homework/submission_detail.html', context)


@login_required
@role_required('teacher')
def check_submission(request, pk):
    submission = get_object_or_404(AssignmentSubmission, pk=pk)

    if request.method == 'POST':
        marks_value = request.POST.get('marks_obtained', '').strip()

        if marks_value:
            try:
                submission.marks_obtained = Decimal(marks_value)
            except InvalidOperation:
                messages.error(request, 'Please enter a valid numeric mark.')
                return render(request, 'homework/check_submission.html', {'submission': submission})

        submission.remarks = request.POST.get('remarks', '')
        submission.is_checked = True
        submission.save()

        messages.success(request, 'Assignment checked successfully.')
        return redirect('homework:assignment_submissions', pk=submission.assignment.id)

    return render(request, 'homework/check_submission.html', {'submission': submission})
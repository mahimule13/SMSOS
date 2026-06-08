from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from apps.accounts.decorators import admin_required, role_required
from .models import Exam, StudentMarks, ReportCard, ExamSchedule

from apps.students.models import Student
from apps.classes.models import Subject, Section



@login_required(login_url='login')
@role_required('teacher')
def teacher_exam_schedule_create(request):
    teacher = request.user.teacher_profile

    # Teacher can create schedules only for sections where they teach.
    allowed_sections = [sa.section_id for sa in teacher.subject_allocations.all()]

    if request.method == 'POST':
        section_id = request.POST.get('section')
        exam_type = request.POST.get('exam_type')
        exam_name = (request.POST.get('exam_name') or '').strip()
        # In UI this is exam_date; also add compatibility for older form field names.
        exam_date = request.POST.get('exam_date') or request.POST.get('start_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        room = (request.POST.get('room') or '').strip()

        subject_ids = request.POST.getlist('subjects')

        if not section_id or not exam_type or not exam_name:
            messages.error(request, 'Section, Exam Type, and Exam Name are required.')
            return redirect('exams:teacher_exam_schedule_create')

        if int(section_id) not in allowed_sections:
            messages.error(request, 'You are not allowed to create exam timetable for this section.')
            return redirect('exams:teacher_exam_schedule_create')

        if not subject_ids:
            messages.error(request, 'Please select at least one subject.')
            return redirect('exams:teacher_exam_schedule_create')

        exam = Exam.objects.create(
            name=exam_name,
            exam_type=exam_type,
            start_date=exam_date,
            end_date=exam_date,
        )

        section = Section.objects.get(id=section_id)

        subjects = Subject.objects.filter(id__in=subject_ids, is_active=True)

        for subj in subjects:
            ExamSchedule.objects.update_or_create(
                exam=exam,
                section=section,
                subject=subj,
                defaults={
                    'exam_date': exam_date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'room': room,
                },
            )

        messages.success(request, 'Exam timetable created successfully.')
        return redirect('exams:teacher_exam_schedule_create')

    sections = Section.objects.filter(id__in=allowed_sections).order_by('class_model__standard', 'name')
    subjects = Subject.objects.filter(is_active=True).order_by('name')

    # Build exam types list from model choices.
    exam_types = Exam.EXAM_TYPES

    context = {
        'sections': sections,
        'subjects': subjects,
        'exam_types': exam_types,
    }
    return render(request, 'exams/teacher_exam_schedule_create.html', context)


@login_required(login_url='login')
@admin_required
def exam_list(request):

    exams = Exam.objects.all().order_by('-start_date')
    context = {'exams': exams}
    return render(request, 'exams/list.html', context)


@login_required(login_url='login')
@admin_required
def create_exam(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        exam_type = request.POST.get('exam_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        exam = Exam.objects.create(
            name=name,
            exam_type=exam_type,
            start_date=start_date,
            end_date=end_date
        )
        
        messages.success(request, 'Exam created successfully')
        return redirect('exams:list')
    
    return render(request, 'exams/create.html')


@login_required(login_url='login')
def exam_detail(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    schedules = ExamSchedule.objects.filter(exam=exam)
    context = {'exam': exam, 'schedules': schedules}
    return render(request, 'exams/detail.html', context)


@login_required(login_url='login')
@role_required('teacher')
def mark_entry(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    teacher = request.user.teacher_profile
    
    subject_allocations = teacher.subject_allocations.all()
    
    if request.method == 'POST':
        section_id = request.POST.get('section')
        subject_id = request.POST.get('subject')
        
        section = Section.objects.get(id=section_id)
        subject = Subject.objects.get(id=subject_id)
        
        students = section.students.all()
        for student in students:
            marks = request.POST.get(f'marks_{student.id}')
            if marks:
                StudentMarks.objects.update_or_create(
                    student=student,
                    exam=exam,
                    subject=subject,
                    defaults={
                        'marks_obtained': float(marks),
                        'entered_by': teacher
                    }
                )
        
        messages.success(request, 'Marks entered successfully')
    
    context = {
        'exam': exam,
        'subject_allocations': subject_allocations,
    }
    return render(request, 'exams/mark_entry.html', context)


@login_required(login_url='login')
@role_required('teacher')
def teacher_mark_entry(request):
    """Schedule-based teacher marks entry.

    Teachers must select an ExamSchedule. Marks are saved against schedule.exam and schedule.subject
    (not just the single active exam).
    """
    teacher = request.user.teacher_profile

    allowed_sections = [sa.section_id for sa in teacher.subject_allocations.all()]

    exam_schedules = (
        ExamSchedule.objects.filter(section__id__in=allowed_sections)
        .select_related('exam', 'subject', 'section')
        .order_by('exam_date', 'start_time')
    )


    exam_schedule = None
    if request.method == 'POST':
        schedule_id = request.POST.get('exam_schedule')
        if schedule_id:
            exam_schedule = get_object_or_404(
                ExamSchedule,
                pk=schedule_id,
                section_id__in=allowed_sections,
            )

            students = exam_schedule.section.students.all()
            for student in students:
                marks = request.POST.get(f'marks_{student.id}')
                if marks is None or marks == '':
                    continue
                StudentMarks.objects.update_or_create(
                    student=student,
                    exam=exam_schedule.exam,
                    subject=exam_schedule.subject,
                    defaults={
                        'marks_obtained': float(marks),
                        'entered_by': teacher,
                    },
                )

            messages.success(request, 'Marks entered successfully')
            return redirect('exams:teacher_mark_entry')

    context = {
        'exam_schedule': exam_schedule,
        'exam_schedules': exam_schedules,
    }
    return render(request, 'exams/teacher_mark_entry.html', context)




@login_required(login_url='login')
@role_required('student')
def student_reportcard(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    
    # Check if user is the student or admin
    if request.user != student.user and not request.user.profile.is_admin():
        return redirect('accounts:profile')
    
    report_cards = ReportCard.objects.filter(student=student).order_by('-exam')
    context = {'student': student, 'report_cards': report_cards}
    return render(request, 'exams/reportcard.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from apps.accounts.decorators import admin_required, role_required
from .models import Exam, StudentMarks, ReportCard, ExamSchedule
from django.conf import settings
from django.db.models import Sum
from apps.exams.utils_reportcard_pdf import compute_reportcard_for_student_exam, build_reportcard_pdf_bytes


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
    """Schedule-based teacher marks entry (multi-subject).

    Teachers select any ExamSchedule row; then we show *all* subjects scheduled for the same
    exam + section, allowing entering marks for every student in that section.
    """
    teacher = request.user.teacher_profile

    allowed_sections = [sa.section_id for sa in teacher.subject_allocations.all()]

    exam_schedules = (
        ExamSchedule.objects.filter(section__id__in=allowed_sections)
        .select_related('exam', 'subject', 'section')
        .order_by('exam_date', 'start_time')
    )

    schedules_message = ''
    if not exam_schedules:
        schedules_message = (
            'No exam schedules found for your allocated sections. '
            'Ask admin to create exam schedules for your classes/sections '
            'or update teacher subject allocations.'
        )

    exam_schedule = None

    exam_subject_schedules = []
    remarks_text = ''
    students = []
    # existing_marks[(student_id, subject_id)] = value
    existing_marks = {}

    # Support GET prefill via querystring: ?exam_schedule=<id>
    if request.method == 'GET':
        schedule_id = request.GET.get('exam_schedule')
    else:
        schedule_id = request.POST.get('exam_schedule')

    if request.method == 'POST':
        remarks_text = (request.POST.get('remarks') or '').strip()

        if schedule_id:

            exam_schedule = get_object_or_404(
                ExamSchedule,
                pk=schedule_id,
                section_id__in=allowed_sections,
            )

            students = exam_schedule.section.students.all().order_by('id')

            exam_subject_schedules = list(
                ExamSchedule.objects.filter(
                    exam=exam_schedule.exam,
                    section=exam_schedule.section,
                )
                .select_related('subject', 'exam')
                .order_by('subject__name')
            )

            # Save (or update) marks for this exam + section for each subject.
            # Input names are marks_{student.id}_{subject.id}
            for student in students:
                for sch in exam_subject_schedules:
                    key = f'marks_{student.id}_{sch.subject.id}'
                    marks = request.POST.get(key)
                    if marks is None or marks == '':
                        continue

                    StudentMarks.objects.update_or_create(
                        student=student,
                        exam=exam_schedule.exam,
                        subject=sch.subject,
                        defaults={
                            'marks_obtained': float(marks),
                            'entered_by': teacher,
                        },
                    )

            # Upsert ReportCard for each affected student after saving all subject marks.

            for student in students:
                computed = compute_reportcard_for_student_exam(student, exam_schedule.exam)
                ReportCard.objects.update_or_create(
                    student=student,
                    exam=exam_schedule.exam,
                    defaults={
                        'total_marks': computed.get('total_marks', 0),
                        'percentage': computed.get('percentage', 0),
                        'grade': computed.get('grade', '-'),
                        'remarks': remarks_text,
                    },
                )

            messages.success(request, 'Marks entered successfully')
            return redirect(f"{request.path}?exam_schedule={exam_schedule.id}")


    # GET (or POST without valid schedule) -> prepare prefill context.
    # Only load students/subjects if schedule_id is valid for this teacher.
    if schedule_id:
        try:
            exam_schedule = get_object_or_404(
                ExamSchedule,
                pk=schedule_id,
                section_id__in=allowed_sections,
            )
        except Exception:
            exam_schedule = None
            messages.error(request, 'Selected exam schedule is not available for your classes.')

        if exam_schedule:
            students = exam_schedule.section.students.all().order_by("roll_number")
            exam_subject_schedules = (
                ExamSchedule.objects.filter(
                    exam=exam_schedule.exam,
                    section=exam_schedule.section,
                )
                .select_related("subject", "exam")
                .order_by("subject__name")
            )

            marks_qs = StudentMarks.objects.filter(
                student__in=students,
                exam=exam_schedule.exam,
            )

            # For template access we keep keys as "<student_id>-<subject_id>" strings.
            existing_marks = {
                f"{m.student_id}-{m.subject_id}": m.marks_obtained
                for m in marks_qs
            }

            report = ReportCard.objects.filter(
                exam=exam_schedule.exam
            ).first()
            remarks_text = report.remarks if report else ""

    context = {
        'exam_schedule': exam_schedule,
        'exam_subject_schedules': exam_subject_schedules,
        'exam_schedules': exam_schedules,
        'students': students,
        'remarks': remarks_text,
        'existing_marks': existing_marks,
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


@login_required(login_url='login')
@role_required('student')
def reportcard_download_pdf(request, student_id, exam_id):
    student = get_object_or_404(Student, pk=student_id)
    # Strict authorization: only the student themself (or admin) can download
    if request.user != student.user and not request.user.profile.is_admin():
        return redirect('accounts:profile')

    exam = get_object_or_404(Exam, pk=exam_id)

    # Compute from StudentMarks so the PDF is always consistent with latest entered marks
    computed = compute_reportcard_for_student_exam(student, exam)
    subject_rows = [(sm.subject.name, float(sm.marks_obtained), float(exam.total_marks)) for sm in computed.get('subjects', [])]

    # Remarks: prefer existing ReportCard if present, else blank
    rc = ReportCard.objects.filter(student=student, exam=exam).order_by('-generated_at').first()
    remarks = rc.remarks if rc else ''

    # School name/logo: optional
    school_name = getattr(settings, 'SCHOOL_NAME', 'School')
    logo_path = getattr(settings, 'SCHOOL_LOGO_PATH', '')

    student_details = {
        'name': student.user.get_full_name(),
        'student_id': student.student_id,
        'class': student.section.class_model.standard,
        'section': student.section.name,
        'roll_no': student.roll_number,
    }

    exam_details = {
        'exam_name': exam.name,
        'exam_date': exam.start_date,
        'total_marks': exam.total_marks,
    }

    pdf_bytes = build_reportcard_pdf_bytes(
        school_name=school_name,
        logo_path=logo_path,
        student_details=student_details,
        exam_details=exam_details,
        subject_rows=subject_rows,
        totals={
            'total_marks': computed.get('total_marks', 0),
            'percentage': computed.get('percentage', 0),
            'grade': computed.get('grade', '-'),
            'result': computed.get('result', '-'),
        },
        remarks=remarks,
    )

    filename = f"reportcard_{student.student_id}_{exam.id}.pdf"
    resp = HttpResponse(pdf_bytes, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date, timedelta
from apps.accounts.decorators import role_required
from .models import Timetable, TeacherTimetable
from apps.classes.models import Section, Subject


@login_required(login_url='login')
@role_required('super_admin', 'school_admin')
def timetable_list(request):
    timetables = Timetable.objects.all().order_by('section', 'day', 'start_time')
    context = {'timetables': timetables}
    return render(request, 'timetable/list.html', context)


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'teacher')
def create_timetable(request):
    user_role = request.user.profile.role.lower()
    section_id = request.GET.get('section') or ''
    allowed_sections = []

    if user_role == 'teacher':
        teacher = request.user.teacher_profile
        allowed_sections = [sa.section_id for sa in teacher.subject_allocations.all()]
    else:
        allowed_sections = list(Section.objects.values_list('id', flat=True))

    if request.method == 'POST':
        section_id = request.POST.get('section')
        subject_id = request.POST.get('subject')
        day = request.POST.get('day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        week_start_date = request.POST.get('week_start_date') or request.POST.get('week')

        if not section_id or not subject_id or not day or not start_time or not end_time or not week_start_date:
            messages.error(request, 'All timetable fields are required.')
            return redirect('timetable:create')

        if int(section_id) not in allowed_sections:
            messages.error(request, 'You are not allowed to create a timetable for this section.')
            return redirect('timetable:create')

        timetable, created = Timetable.objects.update_or_create(
            section_id=section_id,
            week_start_date=week_start_date,
            day=day,
            start_time=start_time,
            defaults={
                'subject_id': subject_id,
                'end_time': end_time,
                'room': request.POST.get('room', '').strip(),
                'teacher': request.user.teacher_profile if user_role == 'teacher' else None,
            }
        )

        messages.success(request, 'Timetable entry saved successfully')
        return redirect('timetable:section', section_id=section_id)

    sections = Section.objects.filter(id__in=allowed_sections).order_by('class_model__standard', 'name')
    subjects = Subject.objects.filter(is_active=True).order_by('name')
    week_start_date = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    context = {
        'sections': sections,
        'subjects': subjects,
        'selected_section_id': section_id,
        'week_start_date': week_start_date,
    }
    return render(request, 'timetable/create.html', context)



@login_required(login_url='login')
def section_timetable(request, section_id):
    section = get_object_or_404(Section, pk=section_id)

    # For now show current calendar week timetable (based on week_start_date).
    # If older entries exist without week_start_date, they will be excluded.
    from datetime import date, timedelta
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    timetables = Timetable.objects.filter(
        section=section,
        week_start_date=week_start,
    ).order_by('day', 'start_time')

    context = {'section': section, 'timetables': timetables}
    return render(request, 'timetable/section.html', context)


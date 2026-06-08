from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import admin_required, role_required
from apps.teachers.models import Teacher
from .models import ClassModel, Section, Subject, SubjectAllocation


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def class_list(request):
    classes = ClassModel.objects.all()
    context = {'classes': classes}
    return render(request, 'classes/list.html', context)


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def create_class(request):
    if request.method == 'POST':
        standard = request.POST.get('standard')
        name = request.POST.get('name')
        
        if ClassModel.objects.filter(standard=standard).exists():
            messages.error(request, 'Class already exists')
        else:
            ClassModel.objects.create(standard=standard, name=name)
            messages.success(request, 'Class created successfully')
            return redirect('classes:list')
    
    return render(request, 'classes/create.html')


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def edit_class(request, pk):
    class_obj = get_object_or_404(ClassModel, pk=pk)
    
    if request.method == 'POST':
        class_obj.name = request.POST.get('name')
        class_obj.standard = request.POST.get('standard')
        class_obj.save()
        messages.success(request, 'Class updated successfully')
        return redirect('classes:list')
    
    context = {'class': class_obj}
    return render(request, 'classes/edit.html', context)


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def delete_class(request, pk):
    class_obj = get_object_or_404(ClassModel, pk=pk)
    class_obj.delete()
    messages.success(request, 'Class deleted successfully')
    return redirect('classes:list')


@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def class_detail(request, pk):
    class_obj = get_object_or_404(ClassModel, pk=pk)
    sections = class_obj.sections.select_related('class_teacher').prefetch_related('subject_allocations__subject', 'subject_allocations__teacher')
    subjects = Subject.objects.filter(is_active=True)
    teachers = Teacher.objects.filter(is_active=True)

    if request.method == 'POST':
        def clean_id(field_name):
            value = request.POST.get(field_name, '')
            if value is None:
                return ''
            return value.strip()

        action = clean_id('action') or 'assign_subject'

        if action == 'assign_subject':
            section_id = clean_id('section')
            subject_id = clean_id('subject')
            teacher_id = clean_id('teacher')

            if not section_id or not subject_id or not teacher_id or not section_id.isdigit() or not subject_id.isdigit() or not teacher_id.isdigit():
                messages.error(request, 'Please select section, subject and teacher before assigning.')
                return redirect('classes:detail', pk=class_obj.pk)

            section = get_object_or_404(Section, pk=section_id, class_model=class_obj)
            subject = get_object_or_404(Subject, pk=subject_id, is_active=True)
            teacher = get_object_or_404(Teacher, pk=teacher_id, is_active=True)

            SubjectAllocation.objects.update_or_create(
                section=section,
                subject=subject,
                defaults={'teacher': teacher}
            )

            messages.success(request, f"Assigned {teacher.user.get_full_name()} to {subject.name} for {section}.")
            return redirect('classes:detail', pk=class_obj.pk)

        if action == 'assign_class_teacher':
            section_id = clean_id('section')
            teacher_id = clean_id('teacher')
            if not section_id or not teacher_id or not section_id.isdigit() or not teacher_id.isdigit():
                messages.error(request, 'Please select section and teacher to set class teacher.')
                return redirect('classes:detail', pk=class_obj.pk)

            section = get_object_or_404(Section, pk=section_id, class_model=class_obj)
            teacher = get_object_or_404(Teacher, pk=teacher_id, is_active=True)

            section.class_teacher = teacher
            section.save()
            messages.success(request, f"Set {teacher.user.get_full_name()} as class teacher for {section}.")
            return redirect('classes:detail', pk=class_obj.pk)

        if action == 'assign_class_incharge':
            teacher_id = clean_id('teacher')
            if not teacher_id or not teacher_id.isdigit():
                messages.error(request, 'Please select a teacher to set as class incharge.')
                return redirect('classes:detail', pk=class_obj.pk)

            teacher = get_object_or_404(Teacher, pk=teacher_id, is_active=True)
            class_obj.class_incharge = teacher
            class_obj.save()
            messages.success(request, f"Set {teacher.user.get_full_name()} as class incharge for {class_obj}.")
            return redirect('classes:detail', pk=class_obj.pk)

    context = {
        'class_obj': class_obj,
        'sections': sections,
        'subjects': subjects,
        'teachers': teachers,
    }
    return render(request, 'classes/detail.html', context)

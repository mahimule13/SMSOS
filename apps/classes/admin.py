from django.contrib import admin
from .models import ClassModel, Section, Subject, SubjectAllocation


@admin.register(ClassModel)
class ClassModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'standard', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'class_teacher', 'capacity', 'is_active')
    list_filter = ('is_active', 'class_model')
    search_fields = ('name', 'class_model__name')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')


@admin.register(SubjectAllocation)
class SubjectAllocationAdmin(admin.ModelAdmin):
    list_display = ('section', 'subject', 'teacher')
    search_fields = ('section', 'subject__name', 'teacher__user__username')

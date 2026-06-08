from django.contrib import admin
from .models import Homework, StudentSubmission


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'section', 'due_date', 'status')
    list_filter = ('status', 'due_date')


@admin.register(StudentSubmission)
class StudentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'homework', 'submission_date', 'marks')
    list_filter = ('submission_date',)

from django.contrib import admin
from .models import Exam, ExamSchedule, StudentMarks, ReportCard


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'start_date', 'is_active')
    list_filter = ('exam_type', 'is_active', 'start_date')


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('exam', 'subject', 'exam_date')
    list_filter = ('exam_date',)


@admin.register(StudentMarks)
class StudentMarksAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'subject', 'marks_obtained')
    list_filter = ('exam', 'subject')


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'grade', 'rank')
    list_filter = ('exam',)

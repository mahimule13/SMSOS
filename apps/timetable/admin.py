from django.contrib import admin
from .models import Timetable, TeacherTimetable


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('section', 'week_start_date', 'day', 'subject', 'start_time', 'end_time')
    list_filter = ('day', 'section', 'week_start_date')


@admin.register(TeacherTimetable)
class TeacherTimetableAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'day', 'subject', 'start_time', 'end_time')
    list_filter = ('day', 'teacher')


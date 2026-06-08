from django.contrib import admin
from .models import AttendanceReport, PrincipalAttendance


@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    list_display = ('month', 'report_type', 'is_generated')
    list_filter = ('report_type', 'month')


@admin.register(PrincipalAttendance)
class PrincipalAttendanceAdmin(admin.ModelAdmin):
    list_display = ('principal', 'date', 'is_present', 'marked_by')
    list_filter = ('date', 'is_present')
    search_fields = ('principal__username', 'principal__first_name', 'principal__last_name')

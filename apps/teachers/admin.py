from django.contrib import admin
from .models import Teacher, TeacherAttendance, TeacherLeaveRequest, TeacherSalary, TeacherPerformance


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'phone', 'qualification', 'is_active')
    list_filter = ('is_active', 'joining_date')
    search_fields = ('user__first_name', 'user__last_name', 'employee_id', 'phone')
    ordering = ('-created_at',)

@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'date', 'is_present')
    list_filter = ('is_present', 'date')
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name')
    ordering = ('-date',)


@admin.register(TeacherLeaveRequest)
class TeacherLeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type', 'start_date')
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name')
    ordering = ('-created_at',)

@admin.register(TeacherSalary)
class TeacherSalaryAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'month', 'net_salary', 'is_paid')
    list_filter = ('is_paid', 'month')
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name')
    ordering = ('-month',)


@admin.register(TeacherPerformance)
class TeacherPerformanceAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'evaluation_date', 'overall_rating')
    list_filter = ('evaluation_date',)
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name')
    ordering = ('-evaluation_date',)
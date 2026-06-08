from django.contrib import admin
from .models import Student, StudentAttendance, StudentPromotions, StudentDocuments


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'section', 'phone', 'is_active')
    list_filter = ('is_active', 'section', 'admission_date')
    search_fields = ('user__first_name', 'user__last_name', 'student_id', 'phone')


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'is_present')
    list_filter = ('is_present', 'date')
    search_fields = ('student__user__first_name', 'student__user__last_name')


@admin.register(StudentPromotions)
class StudentPromotionsAdmin(admin.ModelAdmin):
    list_display = ('student', 'from_section', 'to_section', 'promotion_date')
    list_filter = ('promotion_date',)
    search_fields = ('student__user__first_name', 'student__user__last_name')


@admin.register(StudentDocuments)
class StudentDocumentsAdmin(admin.ModelAdmin):
    list_display = ('student', 'document_type', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('student__user__first_name', 'student__user__last_name')

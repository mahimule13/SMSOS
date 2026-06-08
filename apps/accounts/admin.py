from django.contrib import admin
from .models import UserProfile, PasswordReset, AuditLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'role',
        'school_id',
        'phone',
        'created_at'
    )

    search_fields = (
        'user__username',
        'school_id'
    )

    list_filter = (
        'role',
    )


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'token')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'module', 'ip_address', 'created_at')
    list_filter = ('action', 'module', 'created_at')
    search_fields = ('user__username', 'module', 'description')
    readonly_fields = ('created_at', 'ip_address')

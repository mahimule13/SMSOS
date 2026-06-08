from django.contrib import admin
from .models import DashboardCache


@admin.register(DashboardCache)
class DashboardCacheAdmin(admin.ModelAdmin):
    list_display = ('key', 'last_updated')
    readonly_fields = ('last_updated',)

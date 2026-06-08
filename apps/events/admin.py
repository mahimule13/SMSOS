from django.contrib import admin
from .models import SchoolEvent


@admin.register(SchoolEvent)
class SchoolEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'is_active')
    list_filter = ('event_date', 'is_active')

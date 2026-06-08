from django.contrib import admin
from .models import HostelRoom, HostelAllocation, HostelFee


@admin.register(HostelRoom)
class HostelRoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'capacity', 'floor', 'is_available')
    list_filter = ('room_type', 'floor', 'is_available')


@admin.register(HostelAllocation)
class HostelAllocationAdmin(admin.ModelAdmin):
    list_display = ('student', 'room', 'allocation_date', 'is_active')
    list_filter = ('is_active', 'allocation_date')


@admin.register(HostelFee)
class HostelFeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'total_amount', 'is_paid')
    list_filter = ('is_paid', 'month')

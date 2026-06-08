from django.contrib import admin
from .models import Bus, BusRoute, BusDriver, StudentTransport


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('number', 'capacity', 'model', 'is_active')
    list_filter = ('is_active',)


@admin.register(BusRoute)
class BusRouteAdmin(admin.ModelAdmin):
    list_display = ('route_name', 'bus', 'fare', 'distance')


@admin.register(BusDriver)
class BusDriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_number', 'bus', 'is_active')
    list_filter = ('is_active',)


@admin.register(StudentTransport)
class StudentTransportAdmin(admin.ModelAdmin):
    list_display = ('student', 'bus', 'route', 'is_active')
    list_filter = ('is_active',)

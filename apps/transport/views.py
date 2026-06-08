from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import admin_required
from .models import Bus, BusRoute, StudentTransport
from apps.students.models import Student


@login_required(login_url='login')
@admin_required
def transport_list(request):
    transports = StudentTransport.objects.all()
    context = {'transports': transports}
    return render(request, 'transport/list.html', context)


@login_required(login_url='login')
@admin_required
def bus_list(request):
    buses = Bus.objects.all()
    context = {'buses': buses}
    return render(request, 'transport/bus_list.html', context)


@login_required(login_url='login')
@admin_required
def route_list(request):
    routes = BusRoute.objects.all()
    context = {'routes': routes}
    return render(request, 'transport/routes.html', context)


@login_required(login_url='login')
@admin_required
def allocate_transport(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        bus_id = request.POST.get('bus_id')
        route_id = request.POST.get('route_id')
        
        student = Student.objects.get(id=student_id)
        
        StudentTransport.objects.update_or_create(
            student=student,
            defaults={
                'bus_id': bus_id,
                'route_id': route_id,
            }
        )
        
        messages.success(request, 'Transport allocated successfully')
    
    students = Student.objects.all()
    buses = Bus.objects.all()
    routes = BusRoute.objects.all()
    
    context = {'students': students, 'buses': buses, 'routes': routes}
    return render(request, 'transport/allocate.html', context)

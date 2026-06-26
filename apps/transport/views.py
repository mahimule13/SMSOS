from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Bus, BusRoute, StudentTransport ,BusDriver
from apps.students.models import Student
from apps.teachers.models import Teacher
from datetime import date
from apps.accounts.decorators import role_required
@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')  
def transport_list(request):
    buses = Bus.objects.filter(is_active=True).select_related('driver', 'teacher')
    transports = StudentTransport.objects.filter(is_active=True).select_related('student__user', 'bus__driver', 'route')
    context = {
        'buses': buses,
        'transports': transports,
    }
    return render(request, 'transport/list.html', context)
@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def bus_list(request):
    buses = Bus.objects.all()
    context = {'buses': buses}
    return render(request, 'transport/bus_list.html', context)
@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def route_list(request):
    routes = BusRoute.objects.all()
    context = {'routes': routes}
    return render(request, 'transport/routes.html', context)
@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
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
                'start_date': date.today(),
                'is_active': True,
            }
    )
        
        messages.success(request, 'Transport allocated successfully')
        return redirect('transport:management')
    students = Student.objects.all()
    buses = Bus.objects.all()
    routes = BusRoute.objects.all()
    
    context = {'students': students, 'buses': buses, 'routes': routes}
    return render(request, 'transport/allocate.html', context)
@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def transport_management(request):

    buses = Bus.objects.filter(
        is_active=True
    ).select_related(
        'driver',
        'teacher',
        'teacher__user'
    )

    context = {
        'buses': buses,
        'bus_count': buses.count(),
        'driver_count': BusDriver.objects.filter(
            is_active=True
        ).count(),
        'route_count': BusRoute.objects.count(),
        'student_count': StudentTransport.objects.filter(
            is_active=True
        ).count(),
    }

    return render(
        request,
        'transport/management.html',
        context
    )
@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def bus_students(request, bus_id):

    bus = get_object_or_404(Bus, pk=bus_id)

    students = StudentTransport.objects.filter(
        bus=bus,
        is_active=True
    ).select_related(
        'student__user',
        'route'
    )
    context = {
        'bus': bus,
        'students': students
    }
    return render(
        request,
        'transport/bus_students.html',
        {
            'bus': bus,
            'students': students
        }
    )

@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def edit_bus(request, bus_id):

    bus = get_object_or_404(Bus, pk=bus_id)

    driver = BusDriver.objects.filter(
        bus=bus
    ).first()

    route = BusRoute.objects.filter(
        bus=bus
    ).first()

    if request.method == 'POST':

        # =====================
        # BUS DETAILS
        # =====================

        bus.number = request.POST.get('number')
        bus.capacity = request.POST.get('capacity')
        bus.model = request.POST.get('model')

        teacher_id = request.POST.get('teacher')

        if teacher_id:
            bus.teacher_id = teacher_id
        else:
            bus.teacher = None

        bus.save()

        # =====================
        # DRIVER DETAILS
        # =====================

        if driver:

            driver.name = request.POST.get(
                'driver_name'
            )

            driver.phone = request.POST.get(
                'driver_phone'
            )

            driver.license_number = request.POST.get(
                'license_number'
            )

            driver.license_expiry = request.POST.get(
                'license_expiry'
            )

            driver.save()

        # =====================
        # ROUTE DETAILS
        # =====================

        if route:

            route.route_name = request.POST.get(
                'route_name'
            )

            route.start_point = request.POST.get(
                'start_point'
            )

            route.end_point = request.POST.get(
                'end_point'
            )

            distance = request.POST.get(
                'distance',''
            ).strip()
            if distance:
                route.distance = distance
            route.save()

        messages.success(
            request,
            'Transport details updated successfully'
        )

        return redirect(
            'transport:management'
        )

    teachers = Teacher.objects.filter(
        is_active=True
    )

    context = {
        'bus': bus,
        'driver': driver,
        'route': route,
        'teachers': teachers,
    }

    return render(
        request,
        'transport/edit_bus.html',
        context
    )
@login_required(login_url='login')
@role_required('super_admin', 'school_admin', 'principal')
def add_transport(request):

    if request.method == 'POST':

        # Bus
        bus = Bus.objects.create(
            number=request.POST.get('bus_number'),
            capacity=request.POST.get('capacity'),
            model=request.POST.get('model'),
            teacher_id=request.POST.get('teacher')
        )

        # Driver
        driver = BusDriver.objects.create(
            bus=bus,
            name=request.POST.get('driver_name'),
            phone=request.POST.get('driver_phone'),
            license_number=request.POST.get('license_number'),
            license_expiry=request.POST.get('license_expiry')
        )

        bus.driver = driver
        bus.save()

        # Route
        BusRoute.objects.create(
            bus=bus,
            route_name=request.POST.get('route_name'),
            start_point=request.POST.get('start_point'),
            end_point=request.POST.get('end_point'),
            distance=request.POST.get('distance') or 0
        )

        messages.success(
            request,
            'Transport Added Successfully'
        )

        return redirect('transport:management')

    teachers = Teacher.objects.filter(
        is_active=True
    )

    return render(
        request,
        'transport/add_transport.html',
        {
            'teachers': teachers
        }
    )
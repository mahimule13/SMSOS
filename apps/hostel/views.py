from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import admin_required
from .models import HostelRoom, HostelAllocation
from apps.students.models import Student


@login_required(login_url='login')
@admin_required
def hostel_list(request):
    allocations = HostelAllocation.objects.filter(is_active=True)
    context = {'allocations': allocations}
    return render(request, 'hostel/list.html', context)


@login_required(login_url='login')
@admin_required
def room_list(request):
    rooms = HostelRoom.objects.all()
    context = {'rooms': rooms}
    return render(request, 'hostel/rooms.html', context)


@login_required(login_url='login')
@admin_required
def allocate_room(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        room_id = request.POST.get('room_id')
        
        student = Student.objects.get(id=student_id)
        room = HostelRoom.objects.get(id=room_id)
        
        HostelAllocation.objects.update_or_create(
            student=student,
            defaults={
                'room': room,
            }
        )
        
        messages.success(request, 'Room allocated successfully')
    
    students = Student.objects.all()
    rooms = HostelRoom.objects.filter(is_available=True)
    
    context = {'students': students, 'rooms': rooms}
    return render(request, 'hostel/allocate.html', context)


@login_required(login_url='login')
@admin_required
def hostel_fees(request):
    from .models import HostelFee
    fees = HostelFee.objects.all().order_by('-month')
    context = {'fees': fees}
    return render(request, 'hostel/fees.html', context)

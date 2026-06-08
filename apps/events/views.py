from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import admin_required
from .models import SchoolEvent


@login_required(login_url='login')
def event_list(request):
    events = SchoolEvent.objects.filter(is_active=True).order_by('-event_date')
    context = {'events': events}
    return render(request, 'events/list.html', context)


@login_required(login_url='login')
@admin_required
def create_event(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        event_date = request.POST.get('event_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        location = request.POST.get('location')
        
        SchoolEvent.objects.create(
            title=title,
            description=description,
            event_date=event_date,
            start_time=start_time,
            end_time=end_time,
            location=location,
            organizer=request.user
        )
        
        messages.success(request, 'Event created successfully')
        return redirect('events:list')
    
    return render(request, 'events/create.html')


@login_required(login_url='login')
def event_detail(request, pk):
    event = get_object_or_404(SchoolEvent, pk=pk)
    context = {'event': event}
    return render(request, 'events/detail.html', context)

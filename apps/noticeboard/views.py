from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import admin_required
from .models import Notice, Event


@login_required(login_url='login')
def notice_list(request):
    notices = Notice.objects.filter(is_active=True).order_by('-created_at')
    context = {'notices': notices}
    return render(request, 'noticeboard/list.html', context)


@login_required(login_url='login')
@admin_required
def create_notice(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        priority = request.POST.get('priority')
        
        Notice.objects.create(
            title=title,
            content=content,
            priority=priority,
            created_by=request.user
        )
        
        messages.success(request, 'Notice created successfully')
        return redirect('noticeboard:list')
    
    return render(request, 'noticeboard/create.html')


@login_required(login_url='login')
def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    context = {'notice': notice}
    return render(request, 'noticeboard/detail.html', context)


@login_required(login_url='login')
def event_list(request):
    events = Event.objects.filter(is_active=True).order_by('-event_date')
    context = {'events': events}
    return render(request, 'noticeboard/events.html', context)

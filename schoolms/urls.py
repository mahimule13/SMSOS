from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('rest_framework.urls')),
    path('', include('apps.accounts.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('students/', include('apps.students.urls')),
    path('teachers/', include('apps.teachers.urls')),
    path('classes/', include('apps.classes.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('fees/', include('apps.fees.urls')),

    path('exams/', include('apps.exams.urls')),

    path('timetable/', include('apps.timetable.urls')),
    path('homework/', include('apps.homework.urls')),
    path('noticeboard/', include('apps.noticeboard.urls')),
    path('library/', include('apps.library.urls')),
    path('transport/', include('apps.transport.urls')),
    path('hostel/', include('apps.hostel.urls')),
    path('events/', include('apps.events.urls')),
    path('finance/', include('apps.finance.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "School Management System"
admin.site.site_title = "SMS Admin"
admin.site.index_title = "Welcome to SMS Administration"

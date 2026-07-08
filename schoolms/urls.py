from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
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
    path('password-reset/',auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html',email_template_name='registration/password_reset_email.html',subject_template_name='registration/password_reset_subject.txt',),name='password_reset'),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "School Management System"
admin.site.site_title = "SMS Admin"
admin.site.index_title = "Welcome to SMS Administration"

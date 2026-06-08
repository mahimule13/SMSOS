from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.attendance_dashboard, name='dashboard'),
    path('reports/', views.attendance_reports, name='reports'),
    path('teacher/', views.teacher_attendance, name='teacher_attendance'),
    path('student/', views.student_attendance, name='student_attendance'),
]


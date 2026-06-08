from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list, name='list'),
    path('create/', views.create_teacher, name='create'),
    path('<int:pk>/', views.teacher_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_teacher, name='edit'),
    path('<int:pk>/delete/', views.delete_teacher, name='delete'),
    path('attendance/', views.teacher_attendance, name='attendance'),
    path('leave-requests/', views.leave_requests, name='leave_requests'),
]

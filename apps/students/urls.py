from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='list'),
    path('create/', views.create_student, name='create'),
    path('<int:pk>/', views.student_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_student, name='edit'),
    path('<int:pk>/delete/', views.delete_student, name='delete'),
    path('attendance/', views.attendance_view, name='attendance'),

    path(
        'my-assignments/',
        views.student_assignments,
        name='student_assignments'
    ),

    path(
        'assignments/<int:pk>/submit/',
        views.submit_assignment,
        name='submit_assignment'
    ),
    path(
        'my-submissions/',
        views.my_submissions,
        name='my_submissions'
    ),

    path(
        'submission/<int:pk>/',
        views.assignment_submission_detail,
        name='assignment_submission_detail'
    ),
]


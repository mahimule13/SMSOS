from django.urls import path
from . import views

app_name = 'homework'

urlpatterns = [
    path('', views.homework_list, name='list'),
    path('create/', views.create_homework, name='create'),
    path('<int:pk>/', views.homework_detail, name='detail'),
    path('<int:pk>/submit/', views.submit_homework, name='submit'),
    path('assignment/create/', views.create_assignment, name='create_assignment'),
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:pk>/edit/', views.edit_assignment, name='edit_assignment'),
    path('assignments/<int:pk>/delete/', views.delete_assignment, name='delete_assignment'),
    path('assignments/<int:pk>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('submission/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('submission/<int:pk>/check/', views.check_submission, name='check_submission'),
]

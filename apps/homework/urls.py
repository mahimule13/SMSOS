from django.urls import path
from . import views

app_name = 'homework'

urlpatterns = [
    path('', views.homework_list, name='list'),
    path('create/', views.create_homework, name='create'),
    path('<int:pk>/', views.homework_detail, name='detail'),
    path('<int:pk>/submit/', views.submit_homework, name='submit'),
]

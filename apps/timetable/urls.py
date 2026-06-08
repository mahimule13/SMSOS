from django.urls import path
from . import views

app_name = 'timetable'

urlpatterns = [
    path('', views.timetable_list, name='list'),
    path('create/', views.create_timetable, name='create'),
    path('<int:section_id>/', views.section_timetable, name='section'),
]

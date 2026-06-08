from django.urls import path
from . import views

app_name = 'hostel'

urlpatterns = [
    path('', views.hostel_list, name='list'),
    path('rooms/', views.room_list, name='rooms'),
    path('allocate/', views.allocate_room, name='allocate'),
    path('fees/', views.hostel_fees, name='fees'),
]

from django.urls import path
from . import views

app_name = 'transport'

urlpatterns = [
    path('', views.transport_list, name='list'),
    path('bus/', views.bus_list, name='bus_list'),
    path('routes/', views.route_list, name='routes'),
    path('allocation/', views.allocate_transport, name='allocation'),
]

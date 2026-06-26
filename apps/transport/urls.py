from django.urls import path
from . import views

app_name = 'transport'

urlpatterns = [
    path('', views.transport_list, name='list'),
    path('bus/', views.bus_list, name='bus_list'),
    path('routes/', views.route_list, name='routes'),
    path('allocation/', views.allocate_transport, name='allocation'),
    path(
        'management/',
        views.transport_management,
        name='management'
    ),
    path(
    'bus/<int:bus_id>/students/',
    views.bus_students,
    name='bus_students'
),

path(
    'bus/<int:bus_id>/edit/',
    views.edit_bus,
    name='edit_bus'
),
path(
    'add/',
    views.add_transport,
    name='add_transport'
),
]

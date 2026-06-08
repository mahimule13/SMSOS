from django.urls import path
from . import views

app_name = 'classes'

urlpatterns = [
    path('', views.class_list, name='list'),
    path('create/', views.create_class, name='create'),
    path('<int:pk>/', views.class_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_class, name='edit'),
    path('<int:pk>/delete/', views.delete_class, name='delete'),
]

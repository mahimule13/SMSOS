from django.urls import path
from . import views

app_name = 'noticeboard'

urlpatterns = [
    path('', views.notice_list, name='list'),
    path('create/', views.create_notice, name='create'),
    path('<int:pk>/', views.notice_detail, name='detail'),
    path('events/', views.event_list, name='events'),
]

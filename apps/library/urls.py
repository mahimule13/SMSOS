from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.book_list, name='list'),
    path('issue/', views.issue_book, name='issue'),
    path('return/', views.return_book, name='return'),
    path('reports/', views.library_reports, name='reports'),
]

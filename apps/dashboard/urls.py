from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [

    # ====================================
    # HOME REDIRECT
    # ====================================

    path(
        '',
        views.home_redirect,
        name='home'
    ),

    # ====================================
    # ADMIN DASHBOARD
    # ====================================

    path(
        'admin/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

    # ====================================
    # PRINCIPAL DASHBOARD
    # ====================================

    path(
        'principal/',
        views.principal_dashboard,
        name='principal_dashboard'
    ),

    # ====================================
    # TEACHER DASHBOARD
    # ====================================

    path(
        'teacher/',
        views.teacher_dashboard,
        name='teacher_dashboard'
    ),

    # ====================================
    # STUDENT DASHBOARD
    # ====================================

    path(
        'student/',
        views.student_dashboard,
        name='student_dashboard'
    ),

    # ====================================
    # ACCOUNTANT DASHBOARD
    # ====================================

    path(
        'accountant/',
        views.accountant_dashboard,
        name='accountant_dashboard'
    ),

    # ====================================
    # LIBRARIAN DASHBOARD
    # ====================================

    path(
        'librarian/',
        views.librarian_dashboard,
        name='librarian_dashboard'
    ),

    # ====================================
    # AJAX API
    # ====================================

    path(
        'api/dashboard-data/',
        views.dashboard_data,
        name='dashboard_data'
    ),

]
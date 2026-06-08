from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [

    # ====================================
    # HOME / LANDING PAGES
    # ====================================

    path('', views.index, name='index'),

    path('smsabout/', views.smsabout, name='smsabout'),

    path('services/', views.services, name='services'),

    path('pricing/', views.pricing, name='pricing'),

    # ====================================
    # IVR VOICE CALLS (Teacher Dashboard)
    # ====================================

    path(
        'fee-pending-calls/',
        views.fee_pending_calls,
        name='fee_pending_calls'
    ),

    # Pending Fee IVR (dynamic UI)
    path(
        'ivr/call-fee-parent/',
        views.call_parent_for_fee_student,
        name='call_parent_for_fee_student'
    ),

    path(
        'ivr/call-all-pending-fee-parents/',
        views.call_all_pending_fee_parents,
        name='call_all_pending_fee_parents'
    ),


    path(
        'absent-calls/',
        views.absent_calls,
        name='absent_calls'
    ),

    path(
        'general-calls/',
        views.general_calls,
        name='general_calls'
    ),


    # ====================================
    # AUTHENTICATION
    # ====================================

    path('login/', views.login_view, name='login'),

    path('logout/', views.logout_view, name='logout'),

    path('register/', views.register_view, name='register'),

    # ====================================
    # PROFILE
    # ====================================

    path('profile/', views.profile_view, name='profile'),

    path('profile/edit/', views.edit_profile_view, name='edit_profile'),

    # ====================================
    # PRINCIPAL
    # ====================================

    path(
        'add/principal/',
        views.add_principal,
        name='add_principal'
    ),

    path(
        'principal/create-student-credentials/',
        views.principal_create_student_credentials,
        name='principal_create_student_credentials'
    ),

    # ====================================
    # PASSWORD
    # ====================================

    path(
        'change-password/',
        views.change_password_view,
        name='change_password'
    ),

    path(
        'forgot-password/',
        views.forgot_password_view,
        name='forgot_password'
    ),

    path(
        'reset-password/<str:token>/',
        views.reset_password_view,
        name='reset_password'
    ),
    path('smsstudent/', views.smsstudent, name='smsstudent'),
    path('smsteacher/', views.smsteacher, name='smsteacher'),
    path('smsparent/', views.smsparent, name='smsparent'),
    path('smslibrary/', views.smslibrary, name='smslibrary'),
    path('smsfee/', views.smsfee, name='smsfee'),
    path('smsanalytic/', views.smsanalytic, name='smsanalytic'),

]
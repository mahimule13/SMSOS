from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.finance_dashboard, name='dashboard'),
    path('income/', views.income_list, name='income'),
    path('expense/', views.expense_list, name='expense'),
    path('budget/', views.budget_list, name='budget'),
    path('reports/', views.financial_reports, name='reports'),
]

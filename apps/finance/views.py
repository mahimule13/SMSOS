from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from apps.accounts.decorators import role_required
from .models import Income, Expense, Budget


@login_required(login_url='login')
@role_required('accountant', 'school_admin', 'super_admin')
def finance_dashboard(request):
    total_income = Income.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
    }
    return render(request, 'finance/dashboard.html', context)


@login_required(login_url='login')
@role_required('accountant', 'school_admin')
def income_list(request):
    incomes = Income.objects.all().order_by('-date')
    context = {'incomes': incomes}
    return render(request, 'finance/income.html', context)


@login_required(login_url='login')
@role_required('accountant', 'school_admin')
def expense_list(request):
    expenses = Expense.objects.all().order_by('-date')
    context = {'expenses': expenses}
    return render(request, 'finance/expense.html', context)


@login_required(login_url='login')
@role_required('accountant', 'school_admin')
def budget_list(request):
    budgets = Budget.objects.all()
    context = {'budgets': budgets}
    return render(request, 'finance/budget.html', context)


@login_required(login_url='login')
@role_required('accountant', 'school_admin')
def financial_reports(request):
    context = {}
    return render(request, 'finance/reports.html', context)

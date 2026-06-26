from django.contrib import admin
from .models import IncomeCategory, Income, ExpenseCategory, Expense, Budget


@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date', 'receipt_number')
    list_filter = ('category', 'date')


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date', 'voucher_number', 'bill_attachment')
    list_filter = ('category', 'date')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'year', 'budgeted_amount')
    list_filter = ('year',)

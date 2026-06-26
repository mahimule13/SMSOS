from django.db import models
from django.contrib.auth.models import User


class IncomeCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class Income(models.Model):
    category = models.ForeignKey(IncomeCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    date = models.DateField()
    receipt_number = models.CharField(max_length=50, unique=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.category} - {self.amount}"


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    date = models.DateField()
    voucher_number = models.CharField(max_length=50, unique=True)
    bill_attachment = models.FileField(upload_to='expense_bills/', blank=True, null=True)
    transport_bus_number = models.CharField(max_length=50, blank=True, null=True)
    transport_driver_name = models.CharField(max_length=100, blank=True, null=True)
    transport_route = models.CharField(max_length=150, blank=True, null=True)
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.category} - {self.amount}"


class Budget(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    budgeted_amount = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['category', 'year']
        ordering = ['-year']
        
    def __str__(self):
        return f"{self.category} - {self.year}"

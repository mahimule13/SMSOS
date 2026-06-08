from django.db import models
from django.contrib.auth.models import User


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, unique=True)
    publisher = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    added_date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['title']
        
    def __str__(self):
        return self.title


class BookIssue(models.Model):
    STATUS_CHOICES = (
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('lost', 'Lost'),
    )
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    issued_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_books')
    returned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='returned_books')
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-issued_date']
        
    def __str__(self):
        return f"{self.book} - {self.student}"
    
    @property
    def fine_applicable(self):
        from datetime import date
        if self.status == 'returned':
            if self.returned_date > self.due_date:
                return (self.returned_date - self.due_date).days * 5
        else:
            if date.today() > self.due_date:
                return (date.today() - self.due_date).days * 5
        return 0

from django.db import models

from django.contrib.auth.models import User


class FeeStructure(models.Model):

    class FeeType(models.TextChoices):
        TUITION = 'tuition', 'Tuition'
        TERM1 = 'term1', 'Term 1'
        TERM2 = 'term2', 'Term 2'
        BOOKS = 'books', 'Books'
        LIBRARY = 'library', 'Library'

    class_name = models.CharField(max_length=100)

    fee_type = models.CharField(
        max_length=50,
        choices=FeeType.choices
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['class_name']

    def __str__(self):
        return f"{self.class_name} - {self.fee_type}"

class FeeCollection(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('upi', 'UPI'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('overdue', 'Overdue'),
    )

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='fee_collections')
    fee_structure = models.ForeignKey('FeeStructure', on_delete=models.PROTECT)
    month = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)

    # Bank transfer details (optional, captured only when payment_method == 'bank_transfer')
    account_number = models.CharField(max_length=30, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)

    remarks = models.TextField(blank=True)
    collected_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    class Meta:
        ordering = ['-month']
        unique_together = ['student', 'fee_structure', 'month']
        
    def __str__(self):
        return f"{self.student} - {self.month}"
    
    @property
    def amount_due_balance(self):
        return self.amount_due - self.amount_paid


class FeeReceipt(models.Model):
    fee_collection = models.OneToOneField(FeeCollection, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=50, unique=True)
    issued_date = models.DateField(auto_now_add=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    pdf_file = models.FileField(upload_to='receipts/',null=True,blank=True)
    def __str__(self):
        return self.receipt_number


class FinePenalty(models.Model):
    fee_collection = models.ForeignKey(FeeCollection, on_delete=models.CASCADE, related_name='penalties')
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.fee_collection.student} - {self.fine_amount}"

from django.db import models



class HostelRoom(models.Model):
    ROOM_TYPES = (
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
        ('quad', 'Quad'),
    )
    
    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    capacity = models.PositiveIntegerField()
    floor = models.PositiveIntegerField()
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['floor', 'room_number']
        
    def __str__(self):
        return self.room_number


class HostelAllocation(models.Model):
    student = models.OneToOneField('students.Student', on_delete=models.CASCADE, related_name='hostel_allocation')
    room = models.ForeignKey('HostelRoom', on_delete=models.PROTECT, related_name='allocations')
    allocation_date = models.DateField()
    vacate_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-allocation_date']
        
    def __str__(self):
        return f"{self.student} - {self.room}"


class HostelFee(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='hostel_fees')
    month = models.DateField()
    room_rent = models.DecimalField(max_digits=10, decimal_places=2)
    extra_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'month']
        ordering = ['-month']
        
    def __str__(self):
        return f"{self.student} - {self.month}"

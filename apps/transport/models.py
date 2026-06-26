from django.db import models
from apps.students.models import Student


class Bus(models.Model):
    number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField()
    model = models.CharField(max_length=100, blank=True)
    registration_date = models.DateField()
    is_active = models.BooleanField(default=True)
    teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_buses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['number']
        
    def __str__(self):
        return self.number


class BusRoute(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='routes')
    route_name = models.CharField(max_length=100)
    start_point = models.CharField(max_length=100)
    end_point = models.CharField(max_length=100)
    distance = models.DecimalField(max_digits=5, decimal_places=2)
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['route_name']
        
    def __str__(self):
        return self.route_name


class BusDriver(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    license_number = models.CharField(max_length=20, unique=True)
    license_expiry = models.DateField()
    bus = models.OneToOneField(Bus, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class StudentTransport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='transport')
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='students')
    route = models.ForeignKey(BusRoute, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-start_date']
        
    def __str__(self):
        return f"{self.student} - {self.bus}"

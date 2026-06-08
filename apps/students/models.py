from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import uuid


class Student(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    BLOOD_GROUP_CHOICES = (
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    admission_number = models.CharField(max_length=30, unique=True)
    roll_number = models.CharField(max_length=10)
    
    # Personal information
    dob = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Photo and documents
    photo = models.ImageField(
        upload_to='student_photos/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    aadhar = models.CharField(max_length=12, blank=True)
    
    # Academic information
    section = models.ForeignKey('classes.Section', on_delete=models.CASCADE, related_name='students')
    
    # Parent information
    father_name = models.CharField(max_length=100)
    father_phone = models.CharField(max_length=20)
    mother_name = models.CharField(max_length=100)
    mother_phone = models.CharField(max_length=20)
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    admission_date = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"
    
    def get_age(self):
        from datetime import date
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
    
    def get_attendance_percentage(self):
        from .models import StudentAttendance
        total = StudentAttendance.objects.filter(student=self).count()
        if total == 0:
            return 0
        present = StudentAttendance.objects.filter(student=self, is_present=True).count()
        return (present / total) * 100


class StudentAttendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    is_present = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.student} - {self.date}"


class StudentPromotions(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='promotions')
    from_section = models.ForeignKey('classes.Section', on_delete=models.PROTECT, related_name='promoted_from')
    to_section = models.ForeignKey('classes.Section', on_delete=models.PROTECT, related_name='promoted_to')
    promotion_date = models.DateField()
    remarks = models.TextField(blank=True)
    promoted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-promotion_date']
        
    def __str__(self):
        return f"{self.student} - {self.from_section} to {self.to_section}"


class StudentDocuments(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('birth_certificate', 'Birth Certificate'),
            ('aadhar', 'Aadhar Card'),
            ('vaccination', 'Vaccination Certificate'),
            ('medical', 'Medical Certificate'),
            ('other', 'Other'),
        ]
    )
    document = models.FileField(upload_to='student_documents/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f"{self.student} - {self.get_document_type_display()}"

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator



class Teacher(models.Model):
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

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    # Optional local login credentials (hashed password)
    login_username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    login_password = models.CharField(max_length=128, blank=True)  # store hashed password
    employee_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    dob = models.DateField()
    photo = models.ImageField(
        upload_to='teacher_photos/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    aadhar = models.CharField(max_length=12, unique=True, blank=True)
    pan = models.CharField(max_length=10, unique=True, blank=True)
    
    # Professional details
    qualification = models.CharField(max_length=100)
    specialization = models.ForeignKey('classes.Subject', on_delete=models.SET_NULL, null=True, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    joining_date = models.DateField()
    
    # Salary details
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"
    
    def get_age(self):
        from datetime import date
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))


class TeacherAttendance(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    is_present = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marked_teacher_attendance')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['teacher', 'date']
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.teacher} - {self.date}"
class TeacherLeaveRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    LEAVE_TYPES = (
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('earned', 'Earned Leave'),
        ('study', 'Study Leave'),
    )
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_teacher_leaves')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.teacher} - {self.leave_type} ({self.start_date} to {self.end_date})"
    
    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1


class TeacherSalary(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='salaries')
    month = models.DateField()
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['teacher', 'month']
        ordering = ['-month']
        
    def __str__(self):
        return f"{self.teacher} - {self.month.strftime('%B %Y')}"
    
    def calculate_net_salary(self):
        self.gross_salary = self.base_salary + self.allowances
        self.net_salary = self.gross_salary - self.deductions
        return self.net_salary


class TeacherPerformance(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='performance_reviews')
    evaluation_date = models.DateField()
    academic_performance = models.PositiveIntegerField()  # 0-100
    discipline = models.PositiveIntegerField()  # 0-100
    communication = models.PositiveIntegerField()  # 0-100
    punctuality = models.PositiveIntegerField()  # 0-100
    overall_rating = models.DecimalField(max_digits=3, decimal_places=1)
    comments = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-evaluation_date']
        
    def __str__(self):
        return f"{self.teacher} - {self.evaluation_date}"

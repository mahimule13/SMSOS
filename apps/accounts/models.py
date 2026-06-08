from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


# ==========================================
# USER PROFILE MODEL
# ==========================================

class UserProfile(models.Model):

    USER_ROLES = (

        ('super_admin', 'Super Admin'),
        ('school_admin', 'School Admin'),
        ('principal', 'Principal'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('accountant', 'Accountant'),
        ('librarian', 'Librarian'),

    )

    GENDER_CHOICES = (

        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),

    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    role = models.CharField(
        max_length=30,
        choices=USER_ROLES,
        default='student'
    )

    school_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    school_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=100,
        default='India',
        blank=True,
        null=True
    )

    zip_code = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )

    dob = models.DateField(
        blank=True,
        null=True
    )

    photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png']
            )
        ]
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = ['-created_at']

    def __str__(self):

        return f"{self.user.get_full_name()} - {self.get_role_display()}"

    def is_admin(self):

        return self.role in [
            'super_admin',
            'school_admin'
        ]

    def is_teacher(self):

        return self.role == 'teacher'

    def is_student(self):

        return self.role == 'student'


# ==========================================
# PASSWORD RESET MODEL
# ==========================================

class PasswordReset(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    token = models.CharField(
        max_length=100,
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField()

    is_used = models.BooleanField(
        default=False
    )

    class Meta:

        ordering = ['-created_at']

    def __str__(self):

        return f"Password Reset - {self.user.username}"


# ==========================================
# AUDIT LOG MODEL
# ==========================================

class AuditLog(models.Model):

    ACTION_CHOICES = (

        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('download', 'Download'),
        ('upload', 'Upload'),

    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )

    module = models.CharField(
        max_length=100
    )

    description = models.TextField()

    ip_address = models.GenericIPAddressField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ['-created_at']

        indexes = [

            models.Index(
                fields=['user', '-created_at']
            ),

        ]

    def __str__(self):

        return f"{self.user} - {self.action} - {self.module}"
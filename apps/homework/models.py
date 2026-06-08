from django.db import models
from django.core.validators import FileExtensionValidator


class Homework(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    )
    
    section = models.ForeignKey('classes.Section', on_delete=models.CASCADE, related_name='homework_assignments')
    subject = models.ForeignKey('classes.Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    attachment = models.FileField(upload_to='homework/', blank=True)
    set_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        ordering = ['-due_date']
        
    def __str__(self):
        return self.title


class StudentSubmission(models.Model):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='homework_submissions')
    submission_file = models.FileField(upload_to='submissions/')
    submission_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['homework', 'student']
        ordering = ['-submission_date']
        
    def __str__(self):
        return f"{self.homework} - {self.student}"
    
    @property
    def is_late(self):
        from datetime import datetime
        return self.submission_date.date() > self.homework.due_date

from django.conf import settings
from django.db import models


class PrincipalAttendance(models.Model):
    principal = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='principal_attendances'
    )
    date = models.DateField()
    is_present = models.BooleanField(default=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='principal_attendance_marked_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('principal', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"Principal Attendance - {self.principal.get_full_name()} on {self.date}"


class AttendanceReport(models.Model):
    REPORT_TYPE = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    
    month = models.DateField()
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE)
    is_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-month']
        
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.month}"

from django.db import models
from apps.classes.models import Section
from apps.teachers.models import Teacher


class Timetable(models.Model):
    DAYS = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )

    class Meta:
        ordering = ['week_start_date', 'day', 'start_time']
        unique_together = ['section', 'week_start_date', 'day', 'start_time']

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='timetables')
    week_start_date = models.DateField(null=True, blank=True, help_text="Start date of the calendar week")

    day = models.CharField(max_length=20, choices=DAYS)
    subject = models.ForeignKey('classes.Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.section} - {self.week_start_date} - {self.day} - {self.subject}"



class TeacherTimetable(models.Model):
    DAYS = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='timetables')

    day = models.CharField(max_length=20, choices=DAYS)
    subject = models.ForeignKey('classes.Subject', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    
    class Meta:
        unique_together = ['teacher', 'day', 'start_time']
        ordering = ['day', 'start_time']
        
    def __str__(self):
        return f"{self.teacher} - {self.day}"

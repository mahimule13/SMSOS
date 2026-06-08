from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from apps.students.models import Student
from apps.fees.models import FeeCollection
from apps.exams.models import StudentMarks, ReportCard, Exam
from apps.dashboard.models import DashboardCache
import json


@receiver(post_save, sender=FeeCollection)
def update_fee_analytics_on_payment(sender, instance, created, **kwargs):
    """Update dashboard cache when fee payment is made"""
    cache_key = 'fee_analytics'
    DashboardCache.objects.filter(key=cache_key).delete()


@receiver(post_save, sender=StudentMarks)
def update_report_card_on_marks(sender, instance, created, **kwargs):
    """Update report card when marks are entered"""
    if created or instance.pk:
        exam = instance.exam
        total_marks_avg = StudentMarks.objects.filter(
            student=instance.student,
            exam=exam
        ).aggregate(models.Avg('marks_obtained'))['marks_obtained__avg'] or 0
        
        percentage = (total_marks_avg / exam.total_marks) * 100 if exam.total_marks > 0 else 0
        
        if percentage >= 90:
            grade = 'A+'
        elif percentage >= 80:
            grade = 'A'
        elif percentage >= 70:
            grade = 'B+'
        elif percentage >= 60:
            grade = 'B'
        elif percentage >= 50:
            grade = 'C'
        else:
            grade = 'F'
        
        ReportCard.objects.update_or_create(
            student=instance.student,
            exam=exam,
            defaults={
                'total_marks': total_marks_avg,
                'percentage': percentage,
                'grade': grade,
            }
        )
    
    # Clear dashboard cache
    DashboardCache.objects.filter(key='exam_analytics').delete()


@receiver(post_save, sender=Student)
def update_dashboard_on_student_change(sender, instance, created, **kwargs):
    """Update dashboard cache when student data changes"""
    DashboardCache.objects.filter(key='student_count').delete()

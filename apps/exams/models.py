from django.db import models



class Exam(models.Model):
    EXAM_TYPES = (
        ('slip_test', 'Slip Test'),
        ('week_test', 'Week Test'),
        ('unit_test', 'Unit Test'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half Yearly'),
        ('fa1', 'FA1'),
        ('fa2', 'FA2'),
        ('pre_final', 'Pre Final'),
        ('final', 'Final'),
        ('mid_term', 'Mid Term'),
        ('practical', 'Practical'),
    )

    
    name = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=40)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
        
    def __str__(self):
        return self.name


class ExamSchedule(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='schedules')
    section = models.ForeignKey(
        'classes.Section',
        on_delete=models.CASCADE,
        related_name='exam_schedules',
        null=True,
        blank=True,
    )



    subject = models.ForeignKey('classes.Subject', on_delete=models.CASCADE)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)


    
    class Meta:
        unique_together = ['exam', 'section', 'subject']
        ordering = ['exam_date']

    def __str__(self):
        return f"{self.exam} - {self.subject}"


class StudentMarks(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='marks')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='student_marks')
    subject = models.ForeignKey('classes.Subject', on_delete=models.CASCADE)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    entered_by = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'exam', 'subject']
        
    def __str__(self):
        return f"{self.student} - {self.exam} - {self.subject}"
    
    def get_grade(self):
        exam = self.exam
        percentage = (self.marks_obtained / exam.total_marks) * 100
        
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C'
        else:
            return 'F'


class ReportCard(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='report_cards')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='report_cards')
    total_marks = models.DecimalField(max_digits=5, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2)
    rank = models.PositiveIntegerField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-exam']
        
    def __str__(self):
        return f"{self.student} - {self.exam}"

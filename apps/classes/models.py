from django.db import models

class ClassModel(models.Model):
    name = models.CharField(max_length=50)
    standard = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    class_incharge = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incharge_classes'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['standard']
        unique_together = ['standard']
        
    def __str__(self):
        return f"Class {self.standard}"
    
    def total_students(self):
        # Sum students across all sections for this class
        try:
            return sum(section.total_students() for section in self.sections.all())
        except Exception:
            return 0


class Section(models.Model):
    class_model = models.ForeignKey(ClassModel, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=50)
    class_teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='class_sections')
    capacity = models.PositiveIntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['class_model', 'name']
        unique_together = ['class_model', 'name']
        
    def __str__(self):
        return f"Class {self.class_model.standard} - Section {self.name}"
    
    def total_students(self):
        return self.students.count()


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class SubjectAllocation(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='subject_allocations')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='subject_allocations')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['section', 'subject']
        
    def __str__(self):
        return f"{self.section} - {self.subject} ({self.teacher})"

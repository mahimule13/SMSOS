from django.db import models



class SchoolEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200)
    organizer = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    participants = models.ManyToManyField('students.Student', related_name='events', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-event_date']
        
    def __str__(self):
        return self.title

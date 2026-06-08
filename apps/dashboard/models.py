from django.db import models
from django.db.models import Count, Q, Sum, Avg



class DashboardCache(models.Model):
    """Cache for dynamic dashboard data"""
    key = models.CharField(max_length=255, unique=True)
    value = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_updated']
    
    def __str__(self):
        return self.key

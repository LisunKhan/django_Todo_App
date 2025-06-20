from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class TodoItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True) # Make description optional as in initial assumption
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True) # Allow null for existing rows
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) # Allow null for existing rows
    time_spent = models.IntegerField(default=0, help_text="Time spent in minutes")

    def __str__(self):
        return self.title
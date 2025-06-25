from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class TodoItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    title = models.CharField(max_length=100)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    time_spent = models.IntegerField(default=0)  # Stored in minutes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    task_date = models.DateField(null=True, blank=True)

    @property
    def time_spent_hours(self):
        if self.time_spent is None:
            return 0
        return self.time_spent / 60

    def __str__(self):
        return self.title
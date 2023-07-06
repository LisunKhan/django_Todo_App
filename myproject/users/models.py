from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class TodoItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    title = models.CharField(max_length=100)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    deadline = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True)
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.user.username
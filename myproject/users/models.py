from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum

# Create your models here.
class Task(models.Model):
    """
    The Task model represents a user's task.
    It tracks the user, title, description, estimation time, total spent hours,
    creation and update timestamps, an optional task date, and the current status.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    estimation_time = models.FloatField(default=0)  # in hours
    total_spent_hours = models.FloatField(default=0)  # calculated field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('inprogress', 'In Progress'),
        ('done', 'Done'),
        ('blocker', 'Blocker'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='todo',
    )

    def __str__(self):
        return self.title

    def update_total_spent_hours(self):
        total = self.logs.aggregate(Sum('spent_time'))['spent_time__sum'] or 0
        self.total_spent_hours = total
        self.save(update_fields=['total_spent_hours'])

class TaskLog(models.Model):
    task = models.ForeignKey(Task, related_name='logs', on_delete=models.CASCADE)
    spent_time = models.FloatField()  # in hours
    log_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Log for {self.task.title} on {self.log_date}"

# Project and ProjectMembership Models

class Project(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_projects')
    members = models.ManyToManyField(User, through='ProjectMembership', related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProjectMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f'{self.user.username} - {self.project.name}'

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # For existing users, ensure their profile exists, creating if necessary.
        # Then save it (e.g., to update auto_now fields on the profile if any).
        # This also handles the case where a User might have been created without
        # the signal firing (e.g. loaddata, or if signal was temporarily disconnected)
        profile, created = UserProfile.objects.get_or_create(user=instance)
        if not created:
            # If the profile already existed, we might want to save it if it has
            # auto_now fields or custom save logic that needs to run.
            # However, only save if necessary to avoid extra DB hits.
            # For a simple UserProfile like this one, it might not be strictly needed
            # unless there are fields on UserProfile that are updated by its save() method.
            pass # Or profile.save() if specific conditions require it.

@receiver(post_save, sender=TaskLog)
def update_task_total_spent_on_save(sender, instance, **kwargs):
    instance.task.update_total_spent_hours()

from django.db.models.signals import post_delete

@receiver(post_delete, sender=TaskLog)
def update_task_total_spent_on_delete(sender, instance, **kwargs):
    instance.task.update_total_spent_hours()
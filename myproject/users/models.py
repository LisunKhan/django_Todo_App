from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class TodoItem(models.Model):
    """
    The TodoItem model (also referred to as the Task model) represents a user's task or to-do item.
    It tracks the user, title, description, time spent (in minutes), creation and update timestamps,
    an optional task date, and the current status (To Do, In Progress, or Done). Developers may see
    this model referenced as either TodoItem or Task in documentation or code.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1) # Consider if default=1 is still appropriate
    title = models.CharField(max_length=100)
    description = models.TextField()
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='todo_items')
    time_spent = models.IntegerField(default=0)  # Stored in minutes
    estimation_time = models.IntegerField(default=0) # Stored in minutes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    task_date = models.DateField(null=True, blank=True)

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

    @property
    def time_spent_hours(self):
        if self.time_spent is None:
            return 0
        return self.time_spent / 60

    @property
    def estimation_time_hours(self):
        if self.estimation_time is None:
            return 0
        return self.estimation_time / 60

    def __str__(self):
        return self.title

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
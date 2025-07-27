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
    time_spent = models.FloatField(default=0)  # Stored in hours
    estimation_time = models.FloatField(default=0) # Stored in hours
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

    @property
    def time_spent_hours(self):
        return self.time_spent

    @property
    def estimation_time_hours(self):
        return self.estimation_time

    def __str__(self):
        return self.title

    def update_time_spent(self):
        total_time_hours = self.logs.aggregate(total=models.Sum('log_time'))['total'] or 0
        self.time_spent = total_time_hours
        self.save()

# Project and ProjectMembership Models

class TodoLog(models.Model):
    todo_item = models.ForeignKey(TodoItem, on_delete=models.CASCADE, related_name='logs')
    log_time = models.FloatField(default=0)
    task_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Log for {self.todo_item.title} on {self.task_date}"

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
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender='users.TodoLog')
@receiver(post_delete, sender='users.TodoLog')
def update_todo_time_spent(sender, instance, **kwargs):
    instance.todo_item.update_time_spent()

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
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    title = models.CharField(max_length=100)
    description = models.TextField()
    time_spent = models.IntegerField(default=0)  # Stored in minutes
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

    def __str__(self):
        return self.title

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
        profile, _ = UserProfile.objects.get_or_create(user=instance)
        # If UserProfile has auto_now or auto_now_add fields, or other logic
        # in its save() method that should run when the User is saved,
        # then saving the profile here is important.
        profile.save()
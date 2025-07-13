from django.contrib import admin
from .models import Task, TaskLog, Project, ProjectMembership, UserProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Register your models here.

# Inline for ProjectMembership to be used in ProjectAdmin
class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1 # Number of empty forms to display
    autocomplete_fields = ['user']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'owner__username')
    list_filter = ('owner', 'created_at', 'updated_at')
    inlines = [ProjectMembershipInline]
    autocomplete_fields = ['owner'] # For easier owner selection

@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'date_joined')
    list_filter = ('project', 'user', 'date_joined')
    autocomplete_fields = ['project', 'user']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'user', 'estimation_time', 'total_spent_hours', 'created_at', 'updated_at')
    list_filter = ('status', 'project', 'user', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'total_spent_hours')
    autocomplete_fields = ['user', 'project']

@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    list_display = ('task', 'spent_time', 'log_date', 'created_at')
    list_filter = ('log_date', 'task__project', 'task__user')
    search_fields = ('task__title',)
    autocomplete_fields = ['task']


# If UserProfile is used, it's good to have it in the User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_profile_bio') # Example custom field

    def get_profile_bio(self, instance):
        return instance.profile.bio
    get_profile_bio.short_description = 'Bio'

# Re-register User model
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register UserProfile if you want a separate admin page for it (optional, as it's inlined)
# admin.site.register(UserProfile)

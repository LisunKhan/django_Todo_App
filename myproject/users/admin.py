from django.contrib import admin
from .models import TodoItem

# Register your models here.
class TodoItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'completed', 'user', 'created_at', 'updated_at', 'task_date')
    list_filter = ('completed', 'user', 'created_at', 'updated_at', 'task_date')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(TodoItem, TodoItemAdmin)

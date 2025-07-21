from rest_framework import serializers
from .models import TodoItem, TodoLog, Project

class TodoLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TodoLog
        fields = ['id', 'log_time', 'task_date', 'notes']

class TodoItemSerializer(serializers.ModelSerializer):
    logs = TodoLogSerializer(many=True, read_only=True)

    class Meta:
        model = TodoItem
        fields = ['id', 'title', 'description', 'status', 'project', 'estimation_time', 'time_spent', 'logs', 'created_at', 'updated_at']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'owner', 'members', 'created_at', 'updated_at']

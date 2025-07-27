from rest_framework import serializers
from .models import Project, TodoItem, TodoLog, ProjectMembership
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class ProjectMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = ProjectMembership
        fields = ['user']

class TodoLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TodoLog
        fields = '__all__'

class TodoItemSerializer(serializers.ModelSerializer):
    logs = TodoLogSerializer(many=True, read_only=True)
    class Meta:
        model = TodoItem
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    members = ProjectMembershipSerializer(source='projectmembership_set', many=True)
    class Meta:
        model = Project
        fields = '__all__'

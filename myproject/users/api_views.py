from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Project, TodoItem, TodoLog
from django.contrib.auth.models import User
from datetime import date, timedelta
import json
from django.http import JsonResponse

@login_required
def current_user_api(request):
    return JsonResponse({'user_id': request.user.id})

@login_required
def project_list_api(request):
    projects = Project.objects.filter(members=request.user)
    projects_data = [{'id': project.id, 'name': project.name} for project in projects]
    return JsonResponse(projects_data, safe=False)

@login_required
def project_users_api(request, project_id):
    project = Project.objects.get(id=project_id)
    users = project.members.all()
    users_data = [{'id': user.id, 'username': user.username} for user in users]
    return JsonResponse(users_data, safe=False)

@login_required
def project_tasks_api(request, project_id):
    tasks = TodoItem.objects.filter(project_id=project_id)
    tasks_data = [{
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'user_id': task.user.id,
        'estimation_time': task.estimation_time
    } for task in tasks]
    return JsonResponse(tasks_data, safe=False)

@login_required
def project_logs_api(request, project_id):
    date_param = request.GET.get('date')
    if date_param == 'yesterday':
        log_date = date.today() - timedelta(days=1)
    else:
        log_date = date.today()

    logs = TodoLog.objects.filter(todo_item__project_id=project_id, task_date=log_date)
    logs_data = [{
        'id': log.id,
        'log_time': log.log_time,
        'notes': log.notes,
        'task_id': log.todo_item.id,
        'user_id': log.todo_item.user.id
    } for log in logs]
    return JsonResponse(logs_data, safe=False)

@login_required
def project_blockers_api(request, project_id):
    blockers = TodoItem.objects.filter(project_id=project_id, status='blocker')
    blockers_data = [{
        'id': blocker.id,
        'title': blocker.title,
        'description': blocker.description,
        'user_id': blocker.user.id
    } for blocker in blockers]
    return JsonResponse(blockers_data, safe=False)

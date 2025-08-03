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
    users = project.members.filter(id=request.user.id)
    users_data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
    return JsonResponse(users_data, safe=False)

from django.core.paginator import Paginator

@login_required
def project_tasks_api(request, project_id):
    tasks_query = TodoItem.objects.filter(project_id=project_id, user=request.user)

    search_query = request.GET.get('search')
    if search_query:
        tasks_query = tasks_query.filter(title__icontains=search_query)

    paginator = Paginator(tasks_query, 10) # 10 tasks per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    tasks_data = [{
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'user_id': task.user.id,
        'estimation_time': task.estimation_time,
        'time_spent': task.time_spent
    } for task in page_obj.object_list]

    return JsonResponse({
        'tasks': tasks_data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number
    })

@login_required
def log_time_api_updated(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data['task_id']
        log_time = data['log_time']
        date_str = data.get('date')

        if date_str == 'yesterday':
            log_date = date.today() - timedelta(days=1)
        elif date_str == 'today':
            log_date = date.today()
        else:
            log_date = date_str

        task = TodoItem.objects.get(id=task_id)
        TodoLog.objects.create(
            todo_item=task,
            log_time=log_time,
            task_date=log_date
        )
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def update_log_api_updated(request, log_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        log = TodoLog.objects.get(id=log_id)
        log.log_time = data['log_time']
        log.notes = data['notes']
        if 'task_date' in data:
            log.task_date = data['task_date']
        log.save()

        task = log.todo_item
        task.time_spent = task.logs.aggregate(Sum('log_time'))['log_time__sum'] or 0
        task.save()

        total_log_time_today = task.logs.filter(task_date=date.today()).aggregate(Sum('log_time'))['log_time__sum'] or 0

        return JsonResponse({
            'success': True,
            'total_time_spent': task.time_spent,
            'total_log_time': total_log_time_today,
        })
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def project_tasks_by_date_api(request, project_id, date_str):
    if date_str == 'yesterday':
        log_date = date.today() - timedelta(days=1)
    else:
        log_date = date.today()

    tasks = TodoItem.objects.filter(project_id=project_id, user=request.user, logs__task_date=log_date).distinct()
    tasks_data = []
    for task in tasks:
        total_log_time = task.logs.filter(task_date=log_date).aggregate(Sum('log_time'))['log_time__sum'] or 0
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'user_id': task.user.id,
            'estimation_time': task.estimation_time,
            'time_spent': task.time_spent,
            'total_log_time': total_log_time
        })
    return JsonResponse(tasks_data, safe=False)

from django.db.models import Sum

@login_required
def user_stats_api(request, project_id, user_id, date_str):
    if date_str == 'yesterday':
        log_date = date.today() - timedelta(days=1)
    else:
        log_date = date.today()

    logs = TodoLog.objects.filter(todo_item__project_id=project_id, todo_item__user_id=user_id, task_date=log_date)
    total_time_spent = logs.aggregate(Sum('log_time'))['log_time__sum'] or 0

    tasks = TodoItem.objects.filter(project_id=project_id, user_id=user_id, logs__task_date=log_date).distinct()
    total_estimation_time = tasks.aggregate(Sum('estimation_time'))['estimation_time__sum'] or 0

    return JsonResponse({
        'total_estimation_time': total_estimation_time,
        'total_time_spent': total_time_spent
    })

@login_required
def delete_log_api_updated(request, log_id):
    if request.method == 'POST':
        log = TodoLog.objects.get(id=log_id)
        task = log.todo_item
        log.delete()

        task.time_spent = task.logs.aggregate(Sum('log_time'))['log_time__sum'] or 0
        task.save()

        total_log_time_today = task.logs.filter(task_date=date.today()).aggregate(Sum('log_time'))['log_time__sum'] or 0

        return JsonResponse({
            'success': True,
            'total_time_spent': task.time_spent,
            'total_log_time': total_log_time_today,
        })
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def task_logs_api_updated(request, task_id):
    task = TodoItem.objects.get(id=task_id)
    logs = task.logs.all()
    logs_data = [{'id': log.id, 'log_time': log.log_time, 'notes': log.notes, 'task_date': log.task_date} for log in logs]
    return JsonResponse(logs_data, safe=False)

@login_required
def update_task_log_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data['task_id']
        log_date_str = data['date']

        task = TodoItem.objects.get(id=task_id)

        if log_date_str == 'today':
            log_date = date.today()
        elif log_date_str == 'yesterday':
            log_date = date.today() - timedelta(days=1)
        else:
            # If date is null, it means the task is in the pool, so we delete any existing log for today or yesterday
            TodoLog.objects.filter(todo_item=task, task_date__in=[date.today(), date.today() - timedelta(days=1)], log_time=0).delete()
            return JsonResponse({'success': True})

        # Get or create a log for the task and date
        log, created = TodoLog.objects.get_or_create(
            todo_item=task,
            task_date=log_date,
            defaults={'log_time': 0}
        )

        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

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

@login_required
def create_task_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task = TodoItem.objects.create(
            title=data['title'],
            estimation_time=data['estimation_time'],
            project_id=data['project_id'],
            user=request.user,
            status='todo'
        )
        return JsonResponse({'id': task.id, 'title': task.title, 'description': task.description, 'estimation_time': task.estimation_time, 'status': task.status, 'user_id': task.user.id})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def user_profile_picture_api(request, user_id):
    user = User.objects.get(id=user_id)
    profile = user.profile
    if profile.profile_picture:
        return JsonResponse({'profile_picture_url': profile.profile_picture.url})
    return JsonResponse({'profile_picture_url': None})

from django.db.models import Sum

@login_required
def log_time_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data['task_id']
        log_time = data['log_time']
        task = TodoItem.objects.get(id=task_id)
        TodoLog.objects.create(
            todo_item=task,
            log_time=log_time,
            task_date=date.today()
        )
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def task_total_time_api(request, task_id):
    task = TodoItem.objects.get(id=task_id)
    total_time = task.logs.aggregate(Sum('log_time'))['log_time__sum'] or 0
    return JsonResponse({'total_time': total_time})

@login_required
def task_logs_api(request, task_id):
    task = TodoItem.objects.get(id=task_id)
    logs = task.logs.all()
    logs_data = [{'id': log.id, 'log_time': log.log_time, 'notes': log.notes, 'task_date': log.task_date} for log in logs]
    return JsonResponse(logs_data, safe=False)

@login_required
def update_log_api(request, log_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        log = TodoLog.objects.get(id=log_id)
        log.log_time = data['log_time']
        log.notes = data['notes']
        log.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def delete_log_api(request, log_id):
    if request.method == 'POST':
        log = TodoLog.objects.get(id=log_id)
        log.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def create_log_api(request, task_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        task = TodoItem.objects.get(id=task_id)
        log = TodoLog.objects.create(
            todo_item=task,
            log_time=data['log_time'],
            notes=data['notes'],
            task_date=data['task_date']
        )

        task.time_spent = task.logs.aggregate(Sum('log_time'))['log_time__sum'] or 0
        task.save()

        total_log_time_today = task.logs.filter(task_date=date.today()).aggregate(Sum('log_time'))['log_time__sum'] or 0

        return JsonResponse({
            'success': True,
            'total_time_spent': task.time_spent,
            'total_log_time': total_log_time_today,
        })
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def update_task_log_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data['task_id']
        log_date_str = data['date']

        task = TodoItem.objects.get(id=task_id)

        if log_date_str == 'today':
            log_date = date.today()
        elif log_date_str == 'yesterday':
            log_date = date.today() - timedelta(days=1)
        else:
            # If date is null, it means the task is in the pool, so we delete any existing log for today or yesterday
            TodoLog.objects.filter(todo_item=task, task_date__in=[date.today(), date.today() - timedelta(days=1)], log_time=0).delete()
            return JsonResponse({'success': True})

        # Get or create a log for the task and date
        log, created = TodoLog.objects.get_or_create(
            todo_item=task,
            task_date=log_date,
            defaults={'log_time': 0}
        )

        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

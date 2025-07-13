from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Task, TaskLog, UserProfile
from .forms import TaskForm, TaskLogForm
from django.db.models import Sum, Q
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import JsonResponse
import json
from datetime import date

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('task_list')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

from .models import Project # Make sure Project is imported

@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user)

    current_user = request.user
    user_projects = Project.objects.filter(
        Q(owner=current_user) | Q(members=current_user)
    ).distinct().order_by('name')
    all_projects_data = [{'id': p.id, 'name': p.name} for p in user_projects]

    query = request.GET.get('q')
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(project__name__icontains=query)
        )

    order_by = request.GET.get('order_by', 'task_date')
    allowed_ordering_fields = ['title', 'task_date', 'status', 'project__name',
                               '-title', '-task_date', '-status', '-project__name']
    if order_by not in allowed_ordering_fields:
        order_by = 'task_date'

    status_filter = request.GET.get('status', '')
    start_date_filter = request.GET.get('start_date', '')
    end_date_filter = request.GET.get('end_date', '')
    project_filter_id = request.GET.get('project', '')

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if start_date_filter:
        tasks = tasks.filter(task_date__gte=start_date_filter)
    if end_date_filter:
        tasks = tasks.filter(task_date__lte=end_date_filter)
    if project_filter_id:
        tasks = tasks.filter(project_id=project_filter_id)

    if order_by:
        tasks = tasks.order_by(order_by)

    status_options_list = [{'value': choice[0], 'display': choice[1]} for choice in Task.STATUS_CHOICES]
    status_options_list.insert(0, {'value': '', 'display': 'All Statuses'})

    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'current_order_by': order_by,
        'all_projects': all_projects_data,
        'status_options': status_options_list,
        'selected_status': status_filter,
        'selected_start_date': start_date_filter,
        'selected_end_date': end_date_filter,
        'selected_project_id': int(project_filter_id) if project_filter_id else None,
    }
    return render(request, 'todo/task_list.html', context)

@login_required
def add_task(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        if is_ajax:
            try:
                data = json.loads(request.body)
                form = TaskForm(data, user=request.user)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
        else:
            form = TaskForm(request.POST, user=request.user)

        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()

            if is_ajax:
                serialized_task = {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'status': task.status,
                    'get_status_display': task.get_status_display(),
                    'task_date': task.task_date.strftime('%Y-%m-%d') if task.task_date else None,
                    'estimation_time': task.estimation_time,
                    'total_spent_hours': task.total_spent_hours,
                    'project_id': task.project.id if task.project else None,
                    'project_name': task.project.name if task.project else None,
                }
                return JsonResponse({'success': True, 'task': serialized_task})
            else:
                return redirect('task_list')
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
            else:
                return render(request, 'todo/add_task.html', {'form': form})
    else:
        form = TaskForm(user=request.user)
        if is_ajax:
            return JsonResponse({'error': 'GET request not supported for AJAX here'}, status=405)
        return render(request, 'todo/add_task.html', {'form': form})

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        task.delete()
        if is_ajax:
            return JsonResponse({'success': True})
        else:
            return redirect('task_list')

    return render(request, 'todo/delete_task.html', {'task': task})

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    return render(request, 'todo/task_detail.html', {'task': task})

@login_required
def task_report(request):
    today = date.today()
    # This calculation needs to be updated to use TaskLog
    tasks_for_display = Task.objects.filter(user=request.user, logs__isnull=False).distinct()

    query = request.GET.get('q')
    if query:
        tasks_for_display = tasks_for_display.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(project__name__icontains=query)
        )

    order_by = request.GET.get('order_by', 'task_date')
    allowed_ordering_fields = ['title', 'task_date', 'status', 'total_spent_hours', 'project__name',
                               '-title', '-task_date', '-status', '-total_spent_hours', '-project__name']
    if order_by not in allowed_ordering_fields:
        order_by = 'task_date'

    status_filter = request.GET.get('status', '')
    start_date_filter = request.GET.get('start_date', '')
    end_date_filter = request.GET.get('end_date', '')
    project_filter_id = request.GET.get('project', '')

    if status_filter:
        tasks_for_display = tasks_for_display.filter(status=status_filter)
    if start_date_filter:
        tasks_for_display = tasks_for_display.filter(logs__task_date__gte=start_date_filter)
    if end_date_filter:
        tasks_for_display = tasks_for_display.filter(logs__task_date__lte=end_date_filter)
    if project_filter_id:
        tasks_for_display = tasks_for_display.filter(project_id=project_filter_id)

    if order_by:
        tasks_for_display = tasks_for_display.order_by(order_by)

    status_options = [{'value': choice[0], 'display': choice[1]} for choice in Task.STATUS_CHOICES]
    status_options.insert(0, {'value': '', 'display': 'All Statuses'})

    current_user = request.user
    user_projects = Project.objects.filter(
        Q(owner=current_user) | Q(members=current_user)
    ).distinct().order_by('name')
    project_options = [{'id': p.id, 'name': p.name} for p in user_projects]

    paginator = Paginator(tasks_for_display, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_time_spent_today_hours = TaskLog.objects.filter(task__user=request.user, task_date=today).aggregate(total_time=Sum('spent_time'))['total_time'] or 0


    context = {
        'page_obj': page_obj,
        'total_time_spent_today_hours': total_time_spent_today_hours,
        'query': query,
        'current_order_by': order_by,
        'status_options': status_options,
        'selected_status': status_filter,
        'selected_start_date': start_date_filter,
        'selected_end_date': end_date_filter,
        'project_options': project_options,
        'selected_project_id': int(project_filter_id) if project_filter_id else None,
    }
    return render(request, 'todo/report.html', context)

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            return redirect(reverse('task_detail', args=[task.id]))
    else:
        form = TaskForm(instance=task, user=request.user)
    return render(request, 'todo/edit_task.html', {'form': form, 'task': task})

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def inline_edit_task(request, task_id):
    try:
        task = get_object_or_404(Task, id=task_id, user=request.user)
        data = json.loads(request.body)

        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)

        new_status = data.get('status', task.status)
        if new_status in [choice[0] for choice in Task.STATUS_CHOICES]:
            task.status = new_status

        if 'project_id' in data:
            project_id_val = data['project_id']
            if project_id_val is None or str(project_id_val).lower() == 'null' or str(project_id_val) == '':
                task.project = None
            else:
                try:
                    project_id_int = int(project_id_val)
                    user_accessible_projects = Project.objects.filter(
                        Q(owner=request.user) | Q(members=request.user)
                    ).distinct()
                    project_instance = get_object_or_404(user_accessible_projects, id=project_id_int)
                    task.project = project_instance
                except (ValueError, Project.DoesNotExist):
                    return JsonResponse({'success': False, 'error': 'Project not found or user does not have access.'}, status=404)

        if 'task_date' in data:
            task_date_str = data.get('task_date')
            if task_date_str:
                try:
                    task.task_date = task_date_str
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid date format for task_date. Use YYYY-MM-DD.'}, status=400)
            else:
                task.task_date = None

        if 'estimation_time' in data:
            try:
                hours = float(data['estimation_time'])
                if hours < 0:
                    return JsonResponse({'success': False, 'error': 'Estimation time cannot be negative.'}, status=400)
                task.estimation_time = hours
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Invalid format for estimation_time.'}, status=400)

        task.save()
        task.refresh_from_db()

        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'get_status_display': task.get_status_display(),
                'task_date': task.task_date.strftime('%Y-%m-%d') if task.task_date else None,
                'estimation_time': task.estimation_time,
                'total_spent_hours': task.total_spent_hours,
                'project_id': task.project.id if task.project else None,
                'project_name': task.project.name if task.project else None,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'}, status=500)

@login_required
def profile_view(request):
    # UserProfile is automatically created for each User by a signal
    # So, request.user.profile should exist.
    # If it might not (e.g., if profiles are optional or created differently),
    # you might use: profile, created = UserProfile.objects.get_or_create(user=request.user)
    profile = request.user.profile
    return render(request, 'profile/profile.html', {'profile': profile})

from .forms import UserProfileForm # Import UserProfileForm

@login_required
def edit_profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_view') # Redirect to the profile view page
    else:
        form = UserProfileForm(instance=profile)

    return render(
        request, 'profile/edit_profile.html',
        {
        'form': form,
        'profile': profile,
        'profile_picture_url': profile.profile_picture.url if profile.profile_picture else None
        }
    )

import csv
from django.http import HttpResponse

@login_required
def download_csv_report(request):
    user = request.user
    try:
        profile = user.profile
        user_bio = profile.bio if profile else ""
    except UserProfile.DoesNotExist: # Django raises User.profile.RelatedObjectDoesNotExist if profile doesn't exist
        user_bio = ""

    todo_items = TodoItem.objects.filter(user=user, time_spent__gt=0) # Only include todos with time spent

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="todo_report.csv"'

    writer = csv.writer(response)

    # Write header row
    writer.writerow([
        'Username', 'Email', 'Bio',
        'Todo Title', 'Todo Description', 'Project Name', 'Status',
        'Time Spent (hours)', 'Created At', 'Updated At', 'Task Date'
    ])

    if not todo_items.exists():
        # Write a row with user info even if there are no todos
        writer.writerow([
            user.username, user.email, user_bio,
            'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
        ])
    else:
        for item in todo_items:
            writer.writerow([
                user.username,
                user.email,
                user_bio,
                item.title,
                item.description,
                item.project.name if item.project else 'N/A', # Project Name
                item.get_status_display(),
                item.time_spent_hours,
                item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
                item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else '',
                item.task_date.strftime('%Y-%m-%d') if item.task_date else ''
            ])

    return response


# Kanban Board View
# Note: serializers might be needed if passing complex data initially
# from django.core import serializers

@login_required
def kanban_board_view(request):
    """
    View to render the Kanban board page.
    Initially, it just renders the template.
    Could be extended to pass initial task data (e.g., from TodoItem model).
    """
    # Example: Fetch tasks from database if you want to populate them via Django context
    # user_tasks = TodoItem.objects.filter(user=request.user)
    # context = {
    #    'initial_kanban_tasks_json': serializers.serialize('json', user_tasks)
    # }
    # return render(request, 'users/kanban_board.html', context)

    # For now, just render the template. The JS will handle task creation/display.

    # Fetch projects for the Kanban board's new/edit task forms,
    # filtered by user's ownership or membership.
    current_user = request.user
    user_projects = Project.objects.filter(
        Q(owner=current_user) | Q(members=current_user)
    ).distinct().order_by('name')

    # The template kanban_board.html expects 'kanban_projects_json' for the json_script,
    # which will then be parsed into 'kanban_projects' JS array of objects.
    kanban_projects_data = [{'id': p.id, 'name': p.name} for p in user_projects]

    context = {
        'kanban_projects_json': kanban_projects_data
        # 'initial_kanban_tasks_json' could also be added here if needed
    }
    return render(request, 'users/kanban_board.html', context)


from django.http import JsonResponse, HttpResponseForbidden
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
# Make sure Task and Project are imported if not already:
# from .models import Task, Project

@login_required
def api_get_kanban_tasks(request):
    """
    API endpoint to fetch all tasks for projects the logged-in user is part of (owner or member),
    formatted for the Kanban board.
    """
    current_user = request.user

    user_projects = Project.objects.filter(
        Q(owner=current_user) | Q(members=current_user)
    ).distinct()

    if not user_projects.exists():
        return JsonResponse([], safe=False)

    tasks_query = Task.objects.filter(
        Q(project__in=user_projects) | Q(project__isnull=True, user=current_user)
    ).select_related('user__profile', 'project').order_by('created_at')

    project_id_filter = request.GET.get('project_id')
    if project_id_filter and project_id_filter.lower() != 'all' and project_id_filter.isdigit():
        if user_projects.filter(id=project_id_filter).exists():
            tasks_query = tasks_query.filter(project_id=project_id_filter)
        else:
            return JsonResponse([], safe=False)

    tasks_data = []
    for task in tasks_query:
        profile_picture_url = None
        if hasattr(task.user, 'profile') and task.user.profile.profile_picture:
            profile_picture_url = task.user.profile.profile_picture.url

        tasks_data.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "get_status_display": task.get_status_display(),
            "task_date": task.task_date.strftime('%Y-%m-%d') if task.task_date else None,
            "estimation_time": task.estimation_time,
            "total_spent_hours": task.total_spent_hours,
            "project_id": task.project.id if task.project else None,
            "project_name": task.project.name if task.project else None,
            "user": {
                "username": task.user.username,
                "profile_picture_url": profile_picture_url
            }
        })

    return JsonResponse(tasks_data, safe=False)


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(members=self.request.user).order_by('name')

class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def test_func(self):
        project = self.get_object()
        return self.request.user == project.owner or self.request.user in project.members.all()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name()
            )
        return HttpResponseForbidden("You do not have permission to view this project.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        context['members'] = project.members.all().select_related('profile')
        context['tasks'] = Task.objects.filter(project=project).order_by('status', 'created_at')
        return context

@login_required
def task_logs_api(request, task_id=None, log_id=None):
    if request.method == 'POST':
        data = json.loads(request.body)
        form = TaskLogForm(data)
        if form.is_valid():
            task = get_object_or_404(Task, id=data['task_id'], user=request.user)
            log = form.save(commit=False)
            log.task = task
            log.save()
            return JsonResponse({'id': log.id, 'spent_time': log.spent_time, 'task_date': log.task_date}, status=201)
        return JsonResponse(form.errors, status=400)

    if request.method == 'GET' and task_id:
        task = get_object_or_404(Task, id=task_id, user=request.user)
        logs = task.logs.all().values('id', 'spent_time', 'task_date')
        return JsonResponse(list(logs), safe=False)

    if request.method == 'PUT' and log_id:
        log = get_object_or_404(TaskLog, id=log_id, task__user=request.user)
        data = json.loads(request.body)
        form = TaskLogForm(data, instance=log)
        if form.is_valid():
            log = form.save()
            return JsonResponse({'id': log.id, 'spent_time': log.spent_time, 'task_date': log.task_date})
        return JsonResponse(form.errors, status=400)

    if request.method == 'DELETE' and log_id:
        log = get_object_or_404(TaskLog, id=log_id, task__user=request.user)
        log.delete()
        return JsonResponse({'status': 'deleted'}, status=204)

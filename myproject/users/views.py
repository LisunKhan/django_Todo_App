from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import TodoItem, UserProfile, Project
from .forms import TodoForm
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
            return redirect('todo_list')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

# Removed redundant import of Project

@login_required
def todo_list(request):
    todo_items = TodoItem.objects.filter(user=request.user)

    # Fetch all projects for dropdowns in the template
    projects = Project.objects.all()
    all_projects_data = [{'id': p.id, 'name': p.name} for p in projects]

    # Search
    query = request.GET.get('q')
    if query:
        todo_items = todo_items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(project__name__icontains=query)
        )

    # Ordering
    order_by = request.GET.get('order_by', 'task_date') # Default order by task_date
    # Update allowed_ordering_fields to use 'status' instead of 'completed'
    allowed_ordering_fields = ['title', 'task_date', 'status', 'project__name',
                               '-title', '-task_date', '-status', '-project__name']
    if order_by not in allowed_ordering_fields:
        order_by = 'task_date' # Fallback to default if invalid field is provided

    if order_by:
        # Ensure that if ordering by 'status', it uses the actual field name
        # If 'completed' was a boolean and 'status' is char, direct replacement is fine.
        todo_items = todo_items.order_by(order_by)

    # Pagination
    paginator = Paginator(todo_items, 10) # Show 10 todos per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'current_order_by': order_by,
        'all_projects': all_projects_data, # Pass projects to the template
    }
    return render(request, 'todo/todo_list.html', context)

# @login_required
# def add_todo(request):
#     if request.method == 'POST':
#         title = request.POST['title']
#         todo = TodoItem(title=title)
#         todo.save()
#         return redirect('todo_list')
#     return render(request, 'todo/add_todo.html')

# @login_required
# def add_todo(request):
#     if request.method == 'POST':
#         form = TodoForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('todo_list')
#     else:
#         form = TodoForm()
#     return render(request, 'todo/add_todo.html', {'form': form})

@login_required
def add_todo(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        if is_ajax:
            try:
                data = json.loads(request.body)
                form = TodoForm(data) # Pass data to form
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
        else:
            form = TodoForm(request.POST)

        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()

            if is_ajax:
                # Serialize necessary fields for the frontend
                serialized_todo = {
                    'id': todo.id,
                    'title': todo.title,
                    'description': todo.description,
                    'status': todo.status,
                    'get_status_display': todo.get_status_display(),
                    'task_date': todo.task_date.strftime('%Y-%m-%d') if todo.task_date else None,
                    'time_spent_hours': todo.time_spent_hours,
                    'project_id': todo.project.id if todo.project else None,
                    'project_name': todo.project.name if todo.project else None,
                }
                return JsonResponse({'success': True, 'todo': serialized_todo})
            else:
                return redirect('todo_list')
        else: # Form is invalid
            if is_ajax:
                # form.errors.as_json() returns a JSON string of errors by field
                return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
            else:
                # For non-AJAX, re-render the page with form and errors
                return render(request, 'todo/add_todo.html', {'form': form})
    else: # GET request
        form = TodoForm()
        if is_ajax:
            # Typically, a GET to an 'add' endpoint via AJAX might not be standard,
            # but if needed, could return form structure or similar.
            # For now, let's assume GET AJAX calls are not expected for this view or return an error.
            return JsonResponse({'error': 'GET request not supported for AJAX here'}, status=405) # Method Not Allowed
        return render(request, 'todo/add_todo.html', {'form': form})

@login_required
def delete_todo(request, todo_id):
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        todo.delete()
        if is_ajax:
            return JsonResponse({'success': True})
        else:
            # Fallback for non-AJAX POST, though primarily expecting AJAX now
            return redirect('todo_list')

    # For GET requests, or if not POST (though delete should be POST)
    # This part will be less used if all deletes are via AJAX on the list page.
    # If a user somehow navigates to the delete URL directly via GET.
    return render(request, 'todo/delete_todo.html', {'todo': todo})

# @login_required
# def delete_todo(request, todo_id):
#     todo = get_object_or_404(TodoItem, id=todo_id)
#     if request.method == 'POST':
#         todo.delete()
#         return redirect('todo_list')
#     return render(request, 'todo/delete_todo.html', {'todo': todo})

@login_required
def todo_detail(request, todo_id):
    todo = get_object_or_404(TodoItem, id=todo_id)
    return render(request, 'todo/todo_detail.html', {'todo': todo})

@login_required
def task_report(request):
    # Calculate total time spent on tasks for today by the user
    today = date.today()
    todays_tasks = TodoItem.objects.filter(user=request.user, task_date=today)
    total_time_spent_today_minutes = todays_tasks.aggregate(total_time=Sum('time_spent'))['total_time'] or 0
    total_time_spent_today_hours = total_time_spent_today_minutes / 60

    # Get tasks for display, apply search and ordering
    # This part remains the same, for the main list of tasks displayed in the table
    tasks_for_display = TodoItem.objects.filter(user=request.user, time_spent__gt=0)

    # Search
    query = request.GET.get('q')
    if query:
        tasks_for_display = tasks_for_display.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(project__name__icontains=query)
        )

    # Ordering
    order_by = request.GET.get('order_by', 'task_date') # Default order
    allowed_ordering_fields = ['title', 'task_date', 'status', 'time_spent', 'project__name',
                               '-title', '-task_date', '-status', '-time_spent', '-project__name']
    if order_by not in allowed_ordering_fields:
        order_by = 'task_date' # Fallback to default

    # Get filter parameters
    status_filter = request.GET.get('status', '') # This will be 'todo', 'inprogress', or 'done'
    start_date_filter = request.GET.get('start_date', '')
    end_date_filter = request.GET.get('end_date', '')
    project_filter_id = request.GET.get('project', '')

    # Apply filters
    if status_filter:
        # Filter by the new status field
        tasks_for_display = tasks_for_display.filter(status=status_filter)
    if start_date_filter:
        tasks_for_display = tasks_for_display.filter(task_date__gte=start_date_filter)
    if end_date_filter:
        tasks_for_display = tasks_for_display.filter(task_date__lte=end_date_filter)
    if project_filter_id:
        tasks_for_display = tasks_for_display.filter(project_id=project_filter_id)

    if order_by:
        tasks_for_display = tasks_for_display.order_by(order_by)

    # Get unique statuses for dropdown
    # Updated to use the new status choices from the model
    status_options = [{'value': choice[0], 'display': choice[1]} for choice in TodoItem.STATUS_CHOICES]
    status_options.insert(0, {'value': '', 'display': 'All Statuses'}) # Option to clear filter

    # Get all projects for filter dropdown
    all_projects = Project.objects.all().order_by('name')
    project_options = [{'id': p.id, 'name': p.name} for p in all_projects]

    # Pagination for the displayed tasks
    paginator = Paginator(tasks_for_display, 10) # Show 10 tasks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj, # Paginated tasks
        'total_time_spent_today_hours': total_time_spent_today_hours, # Aggregation for today's tasks
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
def edit_todo(request, todo_id):
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
    if request.method == 'POST':
        form = TodoForm(request.POST, instance=todo)
        if form.is_valid():
            form.save()
            return redirect(reverse('todo_detail', args=[todo.id]))
    else:
        form = TodoForm(instance=todo)
    return render(request, 'todo/edit_todo.html', {'form': form, 'todo': todo})

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST # Ensures this view only accepts POST requests
def inline_edit_todo(request, todo_id):
    try:
        todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
        data = json.loads(request.body)

        todo.title = data.get('title', todo.title)
        todo.description = data.get('description', todo.description)

        # Handle status
        new_status = data.get('status', todo.status)
        if new_status in [choice[0] for choice in TodoItem.STATUS_CHOICES]:
            todo.status = new_status

        # Handle project
        if 'project_id' in data: # Check if project_id key is in the payload
            project_id_val = data['project_id']
            if project_id_val is None or str(project_id_val).lower() == 'null' or str(project_id_val) == '':
                todo.project = None
            else:
                try:
                    project_id_int = int(project_id_val)
                    # Optional: Check if project exists and user has access
                    # from .models import Project
                    # project_instance = Project.objects.get(id=project_id_int)
                    # if not request.user.is_superuser and request.user not in project_instance.members.all():
                    #    return JsonResponse({'success': False, 'error': 'User does not have access to this project.'}, status=403)
                    todo.project_id = project_id_int
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid project_id format.'}, status=400)
                # except Project.DoesNotExist:
                #     return JsonResponse({'success': False, 'error': 'Project not found.'}, status=404)
                except Exception as e:
                    # Log error e for server-side inspection
                    return JsonResponse({'success': False, 'error': f'Could not assign project: {str(e)}'}, status=400)
        # If 'project_id' is not in data, todo.project remains unchanged by this block.

        task_date_str = data.get('task_date')
        if 'task_date' in data: # Check if task_date key is in the payload
            if task_date_str: # Correctly indented
                try:
                    todo.task_date = task_date_str # Django's DateField can parse 'YYYY-MM-DD'
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid date format for task_date. Use YYYY-MM-DD.'}, status=400)
        elif 'task_date' in data and task_date_str is None: # Explicitly setting task_date to null
            todo.task_date = None


        if 'time_spent_hours' in data:
            try:
                hours_str = data['time_spent_hours']
                if hours_str is None or str(hours_str).strip() == '': # Handle null or empty string for time_spent
                    todo.time_spent = 0 # Or None, depending on model definition for time_spent (it's IntegerField default 0)
                else:
                    hours = float(hours_str)
                    if hours < 0:
                        return JsonResponse({'success': False, 'error': 'Time spent cannot be negative.'}, status=400)
                    todo.time_spent = int(hours * 60)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid time format for time_spent_hours.'}, status=400)

        todo.save()
        todo.refresh_from_db()

        return JsonResponse({
            'success': True,
            'todo': {
                'id': todo.id,
                'title': todo.title,
                'description': todo.description,
                'status': todo.status,
                'get_status_display': todo.get_status_display(),
                'task_date': todo.task_date.strftime('%Y-%m-%d') if todo.task_date else None,
                'time_spent_hours': todo.time_spent_hours,
                'project_id': todo.project.id if todo.project else None,
                'project_name': todo.project.name if todo.project else None,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        # Log the exception e
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
            'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A' # Matched N/A count
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

    # Fetch projects for the Kanban board's new/edit task forms
    projects = Project.objects.all()
    # The template kanban_board.html expects 'kanban_projects_json' for the json_script,
    # which will then be parsed into 'kanban_projects' JS array of objects.
    kanban_projects_data = [{'id': p.id, 'name': p.name} for p in projects]

    context = {
        'kanban_projects_json': kanban_projects_data
        # 'initial_kanban_tasks_json' could also be added here if needed
    }
    return render(request, 'users/kanban_board.html', context)


from django.http import JsonResponse
# Make sure TodoItem is imported if not already:
# from .models import TodoItem

@login_required
def api_get_kanban_tasks(request):
    """
    API endpoint to fetch all tasks for the logged-in user,
    formatted for the Kanban board.
    """
    user_tasks = TodoItem.objects.filter(user=request.user).order_by('created_at') # Or any preferred order

    tasks_data = []
    for task in user_tasks:
        tasks_data.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "get_status_display": task.get_status_display(),
            "task_date": task.task_date.strftime('%Y-%m-%d') if task.task_date else None,
            "time_spent_hours": task.time_spent_hours,
            "project_id": task.project.id if task.project else None,
            "project_name": task.project.name if task.project else None,
        })

    return JsonResponse(tasks_data, safe=False)

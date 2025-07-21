from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import TodoItem, UserProfile
from .forms import TodoForm, TodoLogForm
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

from .models import Project # Make sure Project is imported

@login_required
def todo_list(request):
    todo_items = TodoItem.objects.filter(user=request.user)

    # Fetch projects for dropdowns in the template, filtered by user's ownership or membership
    current_user = request.user
    user_projects = Project.objects.filter(
        Q(owner=current_user) | Q(members=current_user)
    ).distinct().order_by('name')
    all_projects_data = [{'id': p.id, 'name': p.name} for p in user_projects]

    # Search
    query = request.GET.get('q')
    if query:
        todo_items = todo_items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(project__name__icontains=query)
        )

    # Ordering
    order_by = request.GET.get('order_by', '-created_at') # Default order by created_at
    # Update allowed_ordering_fields to use 'status' instead of 'completed'
    allowed_ordering_fields = ['title', 'status', 'project__name',
                               '-title', '-status', '-project__name', 'created_at', '-created_at']
    if order_by not in allowed_ordering_fields:
        order_by = '-created_at' # Fallback to default if invalid field is provided

    # Get new filter parameters
    status_filter = request.GET.get('status', '')
    start_date_filter = request.GET.get('start_date', '')
    end_date_filter = request.GET.get('end_date', '')
    project_filter_id = request.GET.get('project', '')

    # Apply new filters
    if status_filter:
        todo_items = todo_items.filter(status=status_filter)
    if start_date_filter:
        todo_items = todo_items.filter(created_at__gte=start_date_filter)
    if end_date_filter:
        todo_items = todo_items.filter(created_at__lte=end_date_filter)
    if project_filter_id:
        todo_items = todo_items.filter(project_id=project_filter_id)

    if order_by:
        # Ensure that if ordering by 'status', it uses the actual field name
        # If 'completed' was a boolean and 'status' is char, direct replacement is fine.
        todo_items = todo_items.order_by(order_by)

    # Status options for the filter dropdown
    status_options_list = [{'value': choice[0], 'display': choice[1]} for choice in TodoItem.STATUS_CHOICES]
    status_options_list.insert(0, {'value': '', 'display': 'All Statuses'})


    # Pagination
    paginator = Paginator(todo_items, 10) # Show 10 todos per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query, # Existing search query
        'current_order_by': order_by, # Existing order_by
        'all_projects': all_projects_data, # Existing projects for create task modal and new project filter
        'status_options': status_options_list, # For the new status filter dropdown
        'selected_status': status_filter,
        'selected_start_date': start_date_filter,
        'selected_end_date': end_date_filter,
        'selected_project_id': int(project_filter_id) if project_filter_id else None,
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
                # Pass user to form for project filtering if applicable
                form = TodoForm(data, user=request.user)
                log_form = TodoLogForm(data)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
        else:
            # Pass user to form for project filtering
            form = TodoForm(request.POST, user=request.user)
            log_form = TodoLogForm(request.POST)

        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()

            if log_form.is_valid() and log_form.cleaned_data.get('log_time'):
                log = log_form.save(commit=False)
                log.todo_item = todo
                log.save()

            if is_ajax:
                # Serialize necessary fields for the frontend
                serialized_todo = {
                    'id': todo.id,
                    'title': todo.title,
                    'description': todo.description,
                    'status': todo.status,
                    'get_status_display': todo.get_status_display(),
                    'time_spent_hours': todo.time_spent_hours,
                    'estimation_time_hours': todo.estimation_time_hours,
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
        # Pass user to form for project filtering for GET requests as well
        form = TodoForm(user=request.user)
        log_form = TodoLogForm()
        if is_ajax:
            # Typically, a GET to an 'add' endpoint via AJAX might not be standard,
            # but if needed, could return form structure or similar.
            # For now, let's assume GET AJAX calls are not expected for this view or return an error.
            return JsonResponse({'error': 'GET request not supported for AJAX here'}, status=405) # Method Not Allowed
        return render(request, 'todo/add_todo.html', {'form': form, 'log_form': log_form})

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
    todays_tasks = TodoItem.objects.filter(user=request.user, created_at__date=today)
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
    order_by = request.GET.get('order_by', '-created_at') # Default order
    allowed_ordering_fields = ['title', 'status', 'time_spent', 'project__name',
                               '-title', '-status', '-time_spent', '-project__name', 'created_at', '-created_at']
    if order_by not in allowed_ordering_fields:
        order_by = '-created_at' # Fallback to default

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
        tasks_for_display = tasks_for_display.filter(created_at__gte=start_date_filter)
    if end_date_filter:
        tasks_for_display = tasks_for_display.filter(created_at__lte=end_date_filter)
    if project_filter_id:
        tasks_for_display = tasks_for_display.filter(project_id=project_filter_id)

    if order_by:
        tasks_for_display = tasks_for_display.order_by(order_by)

    # Get unique statuses for dropdown
    # Updated to use the new status choices from the model
    status_options = [{'value': choice[0], 'display': choice[1]} for choice in TodoItem.STATUS_CHOICES]
    status_options.insert(0, {'value': '', 'display': 'All Statuses'}) # Option to clear filter

    # Get projects for filter dropdown, filtered by user's ownership or membership
    current_user = request.user
    user_projects = Project.objects.filter(
        Q(owner=current_user) | Q(members=current_user)
    ).distinct().order_by('name')
    project_options = [{'id': p.id, 'name': p.name} for p in user_projects]

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
        form = TodoForm(request.POST, instance=todo, user=request.user)
        log_form = TodoLogForm(request.POST)
        if form.is_valid():
            form.save()
            if log_form.is_valid() and log_form.cleaned_data.get('log_time'):
                log = log_form.save(commit=False)
                log.todo_item = todo
                log.save()
            return redirect(reverse('todo_detail', args=[todo.id]))
    else:
        form = TodoForm(instance=todo, user=request.user)
        log_form = TodoLogForm()
    return render(request, 'todo/edit_todo.html', {'form': form, 'log_form': log_form, 'todo': todo})


@login_required
def delete_log(request, log_id):
    log = get_object_or_404(TodoLog, id=log_id, todo_item__user=request.user)
    todo_id = log.todo_item.id
    log.delete()
    return redirect('todo_detail', todo_id=todo_id)


@login_required
def edit_log(request, log_id):
    log = get_object_or_404(TodoLog, id=log_id, todo_item__user=request.user)
    if request.method == 'POST':
        form = TodoLogForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            return redirect('todo_detail', todo_id=log.todo_item.id)
    else:
        form = TodoLogForm(instance=log)
    return render(request, 'todo/edit_log.html', {'form': form, 'log': log})


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
                    # Check if project exists and user has access (owner or member)
                    user_accessible_projects = Project.objects.filter(
                        Q(owner=request.user) | Q(members=request.user)
                    ).distinct()

                    project_instance = get_object_or_404(user_accessible_projects, id=project_id_int)
                    todo.project = project_instance # Assign the validated project instance
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid project_id format.'}, status=400)
                except Project.DoesNotExist:
                     # This error will be raised by get_object_or_404 if project_id_int is not in user_accessible_projects
                    return JsonResponse({'success': False, 'error': 'Project not found or user does not have access.'}, status=404)
                except Exception as e:
                    # Log error e for server-side inspection
                    return JsonResponse({'success': False, 'error': f'Could not assign project: {str(e)}'}, status=500) # 500 for unexpected
        # If 'project_id' is not in data, todo.project remains unchanged by this block.

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

        if 'estimation_time_hours' in data:
            try:
                hours_str = data['estimation_time_hours']
                if hours_str is None or str(hours_str).strip() == '':
                    todo.estimation_time = 0
                else:
                    hours = float(hours_str)
                    if hours < 0:
                        return JsonResponse({'success': False, 'error': 'Estimation time cannot be negative.'}, status=400)
                    todo.estimation_time = int(hours * 60)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid time format for estimation_time_hours.'}, status=400)

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
                'time_spent_hours': todo.time_spent_hours,
                'estimation_time_hours': todo.estimation_time_hours,
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
        'Time Spent (hours)', 'Created At', 'Updated At'
    ])

    if not todo_items.exists():
        # Write a row with user info even if there are no todos
        writer.writerow([
            user.username, user.email, user_bio,
            'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
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
                item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
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
# Make sure TodoItem and Project are imported if not already:
# from .models import TodoItem, Project

@login_required
def api_get_kanban_tasks(request):
    """
    API endpoint to fetch all tasks for projects the logged-in user is part of (owner or member),
    formatted for the Kanban board.
    """
    current_user = request.user

    # Find projects where the user is an owner or a member
    # Q objects are used to combine queries with OR
    user_projects = Project.objects.filter(
        Q(owner=current_user) | Q(members=current_user)
    ).distinct()

    if not user_projects.exists():
        # If the user is not part of any projects, return an empty list
        return JsonResponse([], safe=False)

    # Filter tasks that belong to these projects
    # Also, ensure tasks are selected with related user profile and project for efficiency
    # and ordered by creation date.
    tasks_query = TodoItem.objects.filter(
        Q(project__in=user_projects) | Q(project__isnull=True, user=current_user)
    ).select_related('user__profile', 'project').order_by('created_at')

    # Apply the project filter from the request, if any
    project_id_filter = request.GET.get('project_id')
    if project_id_filter and project_id_filter.lower() != 'all' and project_id_filter.isdigit():
        # Ensure the filtered project is one of the user's projects
        # This prevents users from accessing tasks of projects they are not part of via the filter
        if user_projects.filter(id=project_id_filter).exists():
            tasks_query = tasks_query.filter(project_id=project_id_filter)
        else:
            # If the user tries to filter by a project they are not part of,
            # return an empty list or handle as an error.
            # For simplicity, returning empty list of tasks.
            return JsonResponse([], safe=False)

    tasks_data = []
    for task in tasks_query:
        profile_picture_url = None
        if hasattr(task.user, 'profile') and task.user.profile.profile_picture:
            profile_picture_url = task.user.profile.profile_picture.url
        # else:
            # Optionally, set a default placeholder image URL here
            # profile_picture_url = '/static/images/default_avatar.png'

        tasks_data.append({
            "id": task.id,
            "title": task.title,
            "description": task.description, # Still needed for edit functionality
            "status": task.status,
            "get_status_display": task.get_status_display(),
            "time_spent_hours": task.time_spent_hours,
            "estimation_time_hours": task.estimation_time_hours,
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
    template_name = 'projects/project_list.html'  # Specify your template name
    context_object_name = 'projects'

    def get_queryset(self):
        # Filter projects to only those the current user is a member of
        return Project.objects.filter(members=self.request.user).order_by('name')

class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'  # Specify your template name
    context_object_name = 'project'

    def test_func(self):
        project = self.get_object()
        # Allow access if the user is the owner OR a member of the project
        return self.request.user == project.owner or self.request.user in project.members.all()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name()
            )
        # For authenticated users failing test_func (UserPassesTestMixin)
        return HttpResponseForbidden("You do not have permission to view this project.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        # Add members to context
        context['members'] = project.members.all().select_related('profile')
        # Add tasks associated with this project to the context
        context['tasks'] = TodoItem.objects.filter(project=project).order_by('status', 'created_at')
        return context

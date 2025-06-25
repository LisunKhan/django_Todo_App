from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import TodoItem
from .forms import TodoForm
from django.db.models import Sum, Q
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import JsonResponse
import json

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

@login_required
def todo_list(request):
    todo_items = TodoItem.objects.filter(user=request.user)

    # Search
    query = request.GET.get('q')
    if query:
        todo_items = todo_items.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Ordering
    order_by = request.GET.get('order_by', 'task_date') # Default order by task_date
    allowed_ordering_fields = ['title', 'task_date', 'completed', '-title', '-task_date', '-completed']
    if order_by not in allowed_ordering_fields:
        order_by = 'task_date' # Fallback to default if invalid field is provided

    if order_by:
        todo_items = todo_items.order_by(order_by)

    # Pagination
    paginator = Paginator(todo_items, 10) # Show 10 todos per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'current_order_by': order_by,
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
                    'completed': todo.completed,
                    'task_date': todo.task_date.strftime('%Y-%m-%d') if todo.task_date else None,
                    'time_spent_hours': todo.time_spent_hours, # Using the property
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
    if request.method == 'POST':
        todo.delete()
        return redirect('todo_list')

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
    # Calculate total time spent on ALL tasks for the user (not paginated)
    all_user_tasks = TodoItem.objects.filter(user=request.user)
    total_time_spent_minutes = all_user_tasks.aggregate(total_time=Sum('time_spent'))['total_time'] or 0
    total_time_spent_hours = total_time_spent_minutes / 60

    # Get tasks for display, apply search and ordering
    tasks_for_display = TodoItem.objects.filter(user=request.user)

    # Search
    query = request.GET.get('q')
    if query:
        tasks_for_display = tasks_for_display.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Ordering
    order_by = request.GET.get('order_by', 'task_date') # Default order
    allowed_ordering_fields = ['title', 'task_date', 'completed', 'time_spent', '-title', '-task_date', '-completed', '-time_spent']
    if order_by not in allowed_ordering_fields:
        order_by = 'task_date' # Fallback to default

    if order_by:
        tasks_for_display = tasks_for_display.order_by(order_by)

    # Pagination for the displayed tasks
    paginator = Paginator(tasks_for_display, 10) # Show 10 tasks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj, # Paginated tasks
        'total_time_spent_hours': total_time_spent_hours, # Aggregation from all tasks
        'query': query,
        'current_order_by': order_by,
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
        todo.completed = data.get('completed', todo.completed)

        task_date_str = data.get('task_date')
        if task_date_str:
            try:
                todo.task_date = task_date_str # Django's DateField can parse 'YYYY-MM-DD'
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid date format for task_date. Use YYYY-MM-DD.'}, status=400)
        else:
            todo.task_date = None


        if 'time_spent_hours' in data:
            try:
                hours = float(data['time_spent_hours'])
                if hours < 0:
                    return JsonResponse({'success': False, 'error': 'Time spent cannot be negative.'}, status=400)
                todo.time_spent = int(hours * 60)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid time format.'}, status=400)

        todo.save()
        todo.refresh_from_db() # Ensure all fields are loaded with correct types

        return JsonResponse({
            'success': True,
            'todo': {
                'id': todo.id,
                'title': todo.title,
                'description': todo.description,
                'completed': todo.completed,
                'task_date': todo.task_date.strftime('%Y-%m-%d') if todo.task_date else None,
                'time_spent_hours': todo.time_spent_hours, # Use the property for the response
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        # Log the exception e
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'}, status=500)

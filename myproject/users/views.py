from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import TodoItem
from .forms import TodoForm
from django.db.models import Sum
from django.urls import reverse

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
    todos = TodoItem.objects.filter(user=request.user)
    return render(request, 'todo/todo_list.html', {'todos': todos})

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
    if request.method == 'POST':
        form = TodoForm(request.POST)
        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()
            return redirect('todo_list')
    else:
        form = TodoForm()
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
    tasks = TodoItem.objects.filter(user=request.user)
    total_time_spent_minutes = tasks.aggregate(total_time=Sum('time_spent'))['total_time'] or 0
    total_time_spent_hours = total_time_spent_minutes / 60
    return render(request, 'todo/report.html', {
        'tasks': tasks,
        'total_time_spent_hours': total_time_spent_hours
    })

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

        if 'time_spent_hours' in data:
            try:
                hours = float(data['time_spent_hours'])
                if hours < 0:
                    return JsonResponse({'success': False, 'error': 'Time spent cannot be negative.'}, status=400)
                todo.time_spent = int(hours * 60)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid time format.'}, status=400)

        todo.save()

        return JsonResponse({
            'success': True,
            'todo': {
                'id': todo.id,
                'title': todo.title,
                'description': todo.description,
                'completed': todo.completed,
                'time_spent_hours': todo.time_spent_hours, # Use the property for the response
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        # Log the exception e
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'}, status=500)

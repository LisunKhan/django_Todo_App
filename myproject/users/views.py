from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import TodoItem
from .forms import TodoForm
from django.utils import timezone


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('todo_list')
    else:
        form = AuthenticationForm()
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

# @login_required
# def todo_detail(request, todo_id):
#     todo = get_object_or_404(TodoItem, id=todo_id)
#     return render(request, 'todo/todo_detail.html', {'todo': todo})

@login_required
def todo_detail(request, todo_id):
    todo = get_object_or_404(TodoItem, id=todo_id)
    now = timezone.now()
    remaining_time = todo.deadline - now
    return render(request, 'todo/todo_detail.html', {'todo': todo, 'remaining_time': remaining_time})
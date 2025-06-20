from django.urls import path
from . import views

urlpatterns = [
    # path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('todo_list/', views.todo_list, name='todo_list'),
    path('add_todo/', views.add_todo, name='add_todo'),
    path('delete_todo/<int:todo_id>/', views.delete_todo, name='delete_todo'),
    path('todo_detail/<int:todo_id>/', views.todo_detail, name='todo_detail'),
    path('edit_todo/<int:todo_id>/', views.edit_todo, name='edit_todo'),
    path('toggle_todo_status/<int:todo_id>/', views.toggle_todo_status, name='toggle_todo_status'),
    path('report/', views.view_report, name='view_report'),
]

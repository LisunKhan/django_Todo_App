from django.urls import path
from . import views

urlpatterns = [
    # path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),

    # Project URLs
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),

    path('todo_list/', views.todo_list, name='todo_list'),
    path('add_todo/', views.add_todo, name='add_todo'),
    path('delete_todo/<int:todo_id>/', views.delete_todo, name='delete_todo'),
    path('todo_detail/<int:todo_id>/', views.todo_detail, name='todo_detail'),
    path('todo/<int:todo_id>/edit/', views.edit_todo, name='edit_todo'),
    path('todo/inline_edit/<int:todo_id>/', views.inline_edit_todo, name='inline_edit_todo'),
    path('report/', views.task_report, name='task_report'),
    # Profile URLs
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile_view'),
    path('download_csv_report/', views.download_csv_report, name='download_csv_report'),
    # Kanban Board URL
    path('kanban/', views.kanban_board_view, name='kanban_board'),
    # API URL for fetching Kanban tasks
    path('api/kanban_tasks/', views.api_get_kanban_tasks, name='api_kanban_tasks'),
]

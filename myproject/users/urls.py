from django.urls import path
from . import views

urlpatterns = [
    # path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),

    # Project URLs
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),

    path('task_list/', views.task_list, name='task_list'),
    path('add_task/', views.add_task, name='add_task'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('task_detail/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('task/inline_edit/<int:task_id>/', views.inline_edit_task, name='inline_edit_task'),
    path('report/', views.task_report, name='task_report'),

    # TaskLog API URLs
    path('api/tasklogs/', views.task_logs_api, name='tasklog_create'),
    path('api/tasks/<int:task_id>/logs/', views.task_logs_api, name='tasklog_list'),
    path('api/tasklogs/<int:log_id>/', views.task_logs_api, name='tasklog_detail'),

    # Profile URLs
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile_view'),
    path('download_csv_report/', views.download_csv_report, name='download_csv_report'),
    # Kanban Board URL
    path('kanban/', views.kanban_board_view, name='kanban_board'),
    # API URL for fetching Kanban tasks
    path('api/kanban_tasks/', views.api_get_kanban_tasks, name='api_kanban_tasks'),
]

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
    path('log/<int:log_id>/delete/', views.delete_log, name='delete_log'),
    path('log/<int:log_id>/edit/', views.edit_log, name='edit_log'),
    path('todo/<int:todo_id>/add_log/', views.add_log, name='add_log'),
    path('report/', views.task_report, name='task_report'),
    # Profile URLs
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile_view'),
    path('download_csv_report/', views.download_csv_report, name='download_csv_report'),
    # Kanban Board URL
    path('kanban/', views.kanban_board_view, name='kanban_board'),
    # API URL for fetching Kanban tasks
    path('api/kanban_tasks/', views.api_get_kanban_tasks, name='api_kanban_tasks'),
    # Dashboard
    path('dashboard/project/<int:project_id>/', views.dashboard_view, name='dashboard'),
    # Dashboard APIs
    path('api/dashboard/project/<int:project_id>/users/', views.UserList.as_view(), name='dashboard_user_list'),
    path('api/dashboard/project/<int:project_id>/tasks/', views.ProjectTasks.as_view(), name='dashboard_project_tasks'),
    path('api/dashboard/project/<int:project_id>/logs/', views.ProjectLogs.as_view(), name='dashboard_project_logs'),
    path('api/dashboard/project/<int:project_id>/blockers/', views.ProjectBlockers.as_view(), name='dashboard_project_blockers'),
    path('api/dashboard/task/create/', views.CreateTodoItem.as_view(), name='dashboard_create_task'),
    path('api/dashboard/log/create/', views.CreateTodoLog.as_view(), name='dashboard_create_log'),
    path('api/dashboard/task/update/<int:pk>/', views.UpdateTask.as_view(), name='dashboard_update_task'),
]

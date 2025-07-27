from django.urls import path
from . import views, api_views

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
    # DS Board URL
    path('ds_board/', views.ds_board_view, name='ds_board'),
    # API URL for fetching Kanban tasks
    path('api/kanban_tasks/', views.api_get_kanban_tasks, name='api_kanban_tasks'),
    # DS Board APIs
    path('api/ds_board/current_user/', api_views.current_user_api, name='current_user_api'),
    path('api/ds_board/projects/', api_views.project_list_api, name='project_list_api'),
    path('api/ds_board/project/<int:project_id>/users/', api_views.project_users_api, name='project_users_api'),
    path('api/ds_board/project/<int:project_id>/tasks/', api_views.project_tasks_api, name='project_tasks_api'),
    path('api/ds_board/project/<int:project_id>/logs/', api_views.project_logs_api, name='project_logs_api'),
    path('api/ds_board/project/<int:project_id>/blockers/', api_views.project_blockers_api, name='project_blockers_api'),
    path('api/ds_board/create_task/', api_views.create_task_api, name='create_task_api'),
    path('api/ds_board/user/<int:user_id>/profile_picture/', api_views.user_profile_picture_api, name='user_profile_picture_api'),
]

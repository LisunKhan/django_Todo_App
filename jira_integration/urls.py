from django.urls import path
from . import views

urlpatterns = [
    path('auth/', views.jira_auth, name='jira_auth'),
    path('callback/', views.jira_callback, name='jira_callback'),
    path('projects/', views.get_projects, name='get_projects'),
]

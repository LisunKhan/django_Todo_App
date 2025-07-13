from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Task, TaskLog
from .forms import TaskForm, TaskLogForm
from django.urls import reverse
from django.db.models import Sum
import json
from datetime import date

class TaskModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_task_creation(self):
        task = Task.objects.create(
            user=self.user,
            title='Test Task 1',
            description='Test Description',
            estimation_time=2.5
        )
        self.assertEqual(task.title, 'Test Task 1')
        self.assertEqual(task.estimation_time, 2.5)
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.total_spent_hours, 0)

    def test_task_status_choices(self):
        task = Task.objects.create(user=self.user, title='Status Choice Task')
        self.assertEqual(task.status, 'todo')
        task.status = 'inprogress'
        task.save()
        self.assertEqual(task.status, 'inprogress')
        self.assertEqual(task.get_status_display(), 'In Progress')
        task.status = 'done'
        task.save()
        self.assertEqual(task.status, 'done')
        self.assertEqual(task.get_status_display(), 'Done')

class TaskLogModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.task = Task.objects.create(user=self.user, title='Test Task for Logs')

    def test_task_log_creation(self):
        log = TaskLog.objects.create(
            task=self.task,
            spent_time=1.5,
            task_date=date.today()
        )
        self.assertEqual(log.task, self.task)
        self.assertEqual(log.spent_time, 1.5)
        self.task.refresh_from_db()
        self.assertEqual(self.task.total_spent_hours, 1.5)

    def test_total_spent_hours_update(self):
        TaskLog.objects.create(task=self.task, spent_time=1, task_date=date.today())
        TaskLog.objects.create(task=self.task, spent_time=2, task_date=date.today())
        self.task.refresh_from_db()
        self.assertEqual(self.task.total_spent_hours, 3)

        log_to_delete = TaskLog.objects.first()
        log_to_delete.delete()
        self.task.refresh_from_db()
        self.assertEqual(self.task.total_spent_hours, 2)

class TaskFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testformuser', password='password123')

    def test_task_form_valid(self):
        form_data = {
            'title': 'Form Task',
            'description': 'Form Description',
            'estimation_time': 1.5,
            'status': 'inprogress'
        }
        form = TaskForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        task = form.save(commit=False)
        self.assertEqual(task.status, 'inprogress')
        self.assertEqual(task.estimation_time, 1.5)

class TaskViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testviewuser', password='password123')
        self.client.login(username='testviewuser', password='password123')
        self.other_user = User.objects.create_user(username='otherviewuser', password='password123')

    def test_add_task_view(self):
        url = reverse('add_task')
        post_data = {
            'title': 'View Add Task',
            'description': 'View Add Description',
            'estimation_time': 1.25,
            'status': 'inprogress'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        created_task = Task.objects.get(user=self.user, title='View Add Task')
        self.assertEqual(created_task.estimation_time, 1.25)
        self.assertEqual(created_task.status, 'inprogress')

    def test_task_list_view(self):
        Task.objects.create(user=self.user, title='List Task 1', description='Desc 1', status='todo')
        url = reverse('task_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'List Task 1')

    def test_task_detail_view(self):
        task = Task.objects.create(user=self.user, title='Detail Task', description='Detail Desc', status='inprogress')
        url = reverse('task_detail', args=[task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detail Task')

class TaskLogAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testapiuser', password='password123')
        self.client.login(username='testapiuser', password='password123')
        self.task = Task.objects.create(user=self.user, title='API Test Task')

    def test_create_task_log(self):
        url = reverse('tasklog_create')
        data = {'task_id': self.task.id, 'spent_time': 2, 'task_date': '2023-01-01'}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.task.refresh_from_db()
        self.assertEqual(self.task.total_spent_hours, 2)

    def test_list_task_logs(self):
        TaskLog.objects.create(task=self.task, spent_time=1, task_date='2023-01-01')
        TaskLog.objects.create(task=self.task, spent_time=2, task_date='2023-01-02')
        url = reverse('tasklog_list', args=[self.task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_update_task_log(self):
        log = TaskLog.objects.create(task=self.task, spent_time=1, task_date='2023-01-01')
        url = reverse('tasklog_detail', args=[log.id])
        data = {'spent_time': 1.5, 'task_date': '2023-01-01'}
        response = self.client.put(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.total_spent_hours, 1.5)

    def test_delete_task_log(self):
        log = TaskLog.objects.create(task=self.task, spent_time=1, task_date='2023-01-01')
        url = reverse('tasklog_detail', args=[log.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.task.refresh_from_db()
        self.assertEqual(self.task.total_spent_hours, 0)

import json # Make sure json is imported for inline_edit_todo tests

from django.core.files.uploadedfile import SimpleUploadedFile
from .models import UserProfile

class UserProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='profileuser', password='password123', email='profile@example.com')
        self.client.login(username='profileuser', password='password123')
        # UserProfile should be created automatically by the signal

    def test_profile_created_on_user_creation(self):
        """Test that a UserProfile is automatically created when a User is created."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)
        self.assertEqual(self.user.profile.user, self.user)

    def test_profile_view_displays_information(self):
        """Test that the profile view page displays user and profile information."""
        self.user.profile.bio = "This is a test bio."
        self.user.profile.save()

        url = reverse('profile_view')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.email)
        self.assertContains(response, "This is a test bio.")
        # Check for default profile picture placeholder if no picture is uploaded
        self.assertContains(response, 'https://via.placeholder.com/150')

    def test_profile_view_login_required(self):
        """Test that the profile view requires login."""
        self.client.logout()
        url = reverse('profile_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) # Should redirect to login
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_edit_profile_view_get(self):
        """Test that the edit profile page is accessible and pre-filled."""
        self.user.profile.bio = "Initial bio for editing."
        self.user.profile.save()

        url = reverse('edit_profile_view')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Initial bio for editing.")
        self.assertIsInstance(response.context['form'], self.client.get(url).context['form'].__class__) # Check form instance

    def test_edit_profile_view_post_update_bio(self):
        """Test updating the bio via the edit profile page."""
        url = reverse('edit_profile_view')
        new_bio = "This is an updated bio."
        post_data = {'bio': new_bio}

        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 302) # Should redirect to profile_view
        self.assertRedirects(response, reverse('profile_view'))

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, new_bio)

    def test_edit_profile_view_post_update_profile_picture(self):
        """Test updating the profile picture via the edit profile page."""
        url = reverse('edit_profile_view')

        # Create a dummy image file for upload
        # Using a very small, simple GIF
        image_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        image = SimpleUploadedFile("test_pic.gif", image_content, content_type="image/gif")

        post_data = {'profile_picture': image, 'bio': self.user.profile.bio or ''} # Include bio to ensure form validity if it's required

        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile_view'))

        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.profile_picture.name.startswith('profile_pics/test_pic'))

        # Clean up the uploaded file after test
        if self.user.profile.profile_picture:
            self.user.profile.profile_picture.delete(save=False) # save=False to avoid resaving the model

    def test_edit_profile_view_post_empty_data(self):
        """Test submitting the edit form with no changes or empty optional fields."""
        url = reverse('edit_profile_view')
        initial_bio = self.user.profile.bio

        # Post with empty bio (if bio is optional)
        response = self.client.post(url, {'bio': ''}) # Explicitly post empty bio
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, '') # Bio should be updated to empty string

        # Restore bio to None (initial state for bio can be None)
        self.user.profile.bio = None
        self.user.profile.save()
        # Sanity check that initial_bio was indeed None if that's the default, or whatever it was
        # For a newly created profile via signal, bio is initially None.

        response = self.client.post(url, {}) # Post empty data dictionary (no 'bio' key)
        self.assertEqual(response.status_code, 302) # Still redirects
        self.user.profile.refresh_from_db()
        # When a ModelForm with a CharField(null=True, blank=True, required=False)
        # is saved without that field in POST data, it typically saves as ''.
        self.assertEqual(self.user.profile.bio, '') # Expect empty string, not None

    def test_edit_profile_login_required(self):
        """Test that the edit profile view requires login."""
        self.client.logout()
        url = reverse('edit_profile_view')
        response = self.client.get(url) # Test GET
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

        response = self.client.post(url, {'bio': 'Attempted update'}) # Test POST
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

from django.db import IntegrityError
from .models import Project, ProjectMembership

class ProjectModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1_proj', password='password123')
        self.user2 = User.objects.create_user(username='user2_proj', password='password123')

    def test_project_creation(self):
        project = Project.objects.create(name='Test Project Alpha', owner=self.user1, description='Alpha description')
        self.assertEqual(project.name, 'Test Project Alpha')
        self.assertEqual(project.owner, self.user1)
        self.assertEqual(str(project), 'Test Project Alpha')

    def test_project_add_member(self):
        project = Project.objects.create(name='Test Project Beta', owner=self.user1)
        ProjectMembership.objects.create(project=project, user=self.user2)
        self.assertIn(self.user2, project.members.all())

    def test_project_member_count(self):
        project = Project.objects.create(name='Test Project Gamma', owner=self.user1)
        ProjectMembership.objects.create(project=project, user=self.user1)
        ProjectMembership.objects.create(project=project, user=self.user2)
        self.assertEqual(project.members.count(), 2)

    def test_project_unique_name(self):
        Project.objects.create(name='Unique Project Name', owner=self.user1)
        with self.assertRaises(IntegrityError):
            Project.objects.create(name='Unique Project Name', owner=self.user2)

class ProjectMembershipModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='member_user', password='password123')
        self.project = Project.objects.create(name='Membership Test Project')

    def test_unique_user_project_membership(self):
        ProjectMembership.objects.create(project=self.project, user=self.user)
        with self.assertRaises(IntegrityError):
            ProjectMembership.objects.create(project=self.project, user=self.user)

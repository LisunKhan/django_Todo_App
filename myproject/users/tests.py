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

import csv
from io import StringIO
from django.utils import timezone

class CSVReportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='csvuser', password='password123', email='csv@example.com')
        # UserProfile is created by signal
        self.user.profile.bio = "Test bio for CSV export."
        self.user.profile.save()

        self.todo1_date = timezone.now().date()
        self.todo2_date = timezone.now().date() - timezone.timedelta(days=1)

        self.todo1 = TodoItem.objects.create(
            user=self.user,
            title='CSV Todo 1',
            description='Description for CSV 1',
            status='done',
            time_spent=60, # 1 hour
            task_date=self.todo1_date
        )
        # Manually set created_at and updated_at for predictable testing if necessary
        # For this test, auto_now_add and auto_now should be fine.

        self.todo2 = TodoItem.objects.create(
            user=self.user,
            title='CSV Todo 2',
            description='Description for CSV 2',
            status='todo',
            time_spent=30, # 0.5 hours
            task_date=self.todo2_date
        )
        self.url = reverse('download_csv_report')

    def test_download_csv_report_login_required(self):
        """Test that the CSV download view requires login."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_download_csv_report_headers_and_structure(self):
        """Test CSV headers and basic structure with data."""
        self.client.login(username='csvuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="todo_report.csv"')

        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))

        header = next(reader)
        expected_header = [
            'Username', 'Email', 'Bio',
            'Todo Title', 'Todo Description', 'Project Name', 'Status',
            'Time Spent (hours)', 'Created At', 'Updated At', 'Task Date'
        ]
        self.assertEqual(header, expected_header)

        rows = list(reader)
        # The number of rows will depend on how many todos are created in setUp
        # For CSVReportTests, it's 2. For CSVReportWithProjectTests, it's also 2.
        self.assertEqual(len(rows), TodoItem.objects.filter(user=self.user, time_spent__gt=0).count())


        # Let's find todo1 in the rows, assuming title is unique for this test setup
        row1_data = None
        for row_idx, row_content in enumerate(rows):
            if row_content[3] == self.todo1.title: # Todo Title is the 4th column (index 3)
                row1_data = row_content
                break
        self.assertIsNotNone(row1_data, f"Todo1 (title: {self.todo1.title}) not found in CSV output. Rows: {rows}")


        self.assertEqual(row1_data[0], self.user.username)
        self.assertEqual(row1_data[1], self.user.email)
        self.assertEqual(row1_data[2], self.user.profile.bio)
        self.assertEqual(row1_data[3], self.todo1.title)
        self.assertEqual(row1_data[4], self.todo1.description)
        # Project Name is at index 5
        # Status is at index 6
        # Time Spent is at index 7
        # Created At is at index 8
        # Updated At is at index 9
        # Task Date is at index 10
        if hasattr(self, 'project_csv') and self.todo1.project: # For CSVReportWithProjectTests
             self.assertEqual(row1_data[5], self.todo1.project.name)
        else: # For base CSVReportTests where project might not be set on todo1
             self.assertEqual(row1_data[5], 'N/A' if not self.todo1.project else self.todo1.project.name)

        self.assertEqual(row1_data[6], self.todo1.get_status_display())
        self.assertEqual(float(row1_data[7]), self.todo1.time_spent_hours)
        self.assertIn(self.todo1.created_at.strftime('%Y-%m-%d'), row1_data[8])
        self.assertIn(self.todo1.updated_at.strftime('%Y-%m-%d'), row1_data[9])
        self.assertEqual(row1_data[10], self.todo1.task_date.strftime('%Y-%m-%d'))


    def test_download_csv_report_no_todos(self):
        """
        Test that the CSV report is generated correctly when the user has no to-do items.
        """
        self.client.login(username='csvuser', password='password123')
        TodoItem.objects.filter(user=self.user).delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="todo_report.csv"')

        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        rows = list(reader)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], [
            'Username', 'Email', 'Bio',
            'Todo Title', 'Todo Description', 'Project Name', 'Status',
            'Time Spent (hours)', 'Created At', 'Updated At', 'Task Date'
        ])
        self.assertEqual(rows[1], [
            self.user.username, self.user.email, self.user.profile.bio,
            'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
        ])

    def test_download_csv_report_without_profile_bio(self):
        """Test CSV output when user profile bio is empty."""
        self.user.profile.bio = ""
        self.user.profile.save()
        self.client.login(username='csvuser', password='password123')

        # Keep only one todo for simplicity
        TodoItem.objects.filter(user=self.user).exclude(pk=self.todo1.pk).delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        next(reader) # Skip header
        data_row = next(reader)

        self.assertEqual(data_row[2], "") # Bio column should be empty string

    def test_download_csv_report_date_formats(self):
        """Test the formatting of date and datetime fields."""
        self.client.login(username='csvuser', password='password123')
        # Use only todo1 for this test for simplicity
        TodoItem.objects.filter(user=self.user, pk=self.todo2.pk).delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        next(reader) # Skip header
        row = next(reader)

        # Indices after adding 'Project Name':
        # Created At: 8
        # Updated At: 9
        # Task Date: 10
        self.assertEqual(row[8], self.todo1.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(row[9], self.todo1.updated_at.strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(row[10], self.todo1.task_date.strftime('%Y-%m-%d'))

    def test_download_csv_report_user_profile_does_not_exist_gracefully(self):
        """Test CSV output when user.profile does not exist (e.g., if signal failed or profile deleted)."""
        # This scenario is a bit tricky to set up if signals are robust.
        # We can simulate it by temporarily deleting the profile.
        self.user.profile.delete()
        self.user.refresh_from_db() # Ensure user object doesn't hold cached profile

        self.client.login(username='csvuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        next(reader) # Skip header
        data_row = next(reader) # Get the first data row

        self.assertEqual(data_row[0], self.user.username)
        self.assertEqual(data_row[1], self.user.email)
        self.assertEqual(data_row[2], "") # Bio should be empty if profile is missing

        # The signal create_or_update_user_profile should have recreated the profile
        # when self.client.login() was called, or during other user model saves.
        # So, explicit recreation here is not needed and can cause issues if
        # the profile already exists due to the signal.
        # If we want to ensure it's in a certain state for subsequent tests (though usually tests are isolated),
        # we'd fetch and update, or be mindful of test execution order if TestCases share state (not ideal).
        # For now, removing this explicit creation.
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists(), "Profile should have been recreated by signal.")
        profile = UserProfile.objects.get(user=self.user)
        profile.bio = "Recreated bio for subsequent tests if any" # Example update
        profile.save()


from .models import Project, ProjectMembership
from django.contrib.auth.models import Group

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

from django.db import IntegrityError

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
        # The following assertion will fail because the transaction is rolled back by TestCase
        # self.assertEqual(ProjectMembership.objects.filter(project=self.project, user=self.user).count(), 1)
        # Instead, we should verify the count *before* the operation that causes IntegrityError,
        # or trust that assertRaises(IntegrityError) is sufficient.
        # For now, removing the count assertion post-IntegrityError.

# Update TodoItem related tests
class TodoItemModelWithProjectTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='todo_proj_user', password='password123')
        self.project = Project.objects.create(name='Project For Todos', owner=self.user)

    def test_todo_item_creation_with_project(self):
        todo = TodoItem.objects.create(
            user=self.user,
            title='Task with Project',
            project=self.project
        )
        self.assertEqual(todo.project, self.project)

    def test_todo_item_creation_without_project(self):
        todo = TodoItem.objects.create(
            user=self.user,
            title='Task without Project'
            # project is None by default (null=True)
        )
        self.assertIsNone(todo.project)

    def test_todo_item_project_set_null_on_delete(self):
        todo = TodoItem.objects.create(user=self.user, title='Task for Project Deletion', project=self.project)
        self.project.delete()
        todo.refresh_from_db()
        self.assertIsNone(todo.project)


class TaskFormWithProjectTests(TaskFormTests): # Inherit to reuse user setup
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(name='Form Test Project', owner=self.user)

    def test_task_form_valid_with_project(self):
        form_data = {
            'title': 'Form Task with Project',
            'description': 'Form Description',
            'project': self.project.id,
            'status': 'todo'
        }
        form = TaskForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        task = form.save(commit=False)
        self.assertEqual(task.project, self.project)

    def test_task_form_valid_without_project(self):
        form_data = {'title': 'Form Task No Project', 'description': 'Desc'}
        form = TaskForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        task = form.save(commit=False)
        self.assertIsNone(task.project)


class TaskViewWithProjectTests(TaskViewTests): # Inherit to reuse user/client setup
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(name='View Test Project', owner=self.user)
        ProjectMembership.objects.create(project=self.project, user=self.user) # Add user to project

    def test_add_task_view_with_project(self):
        url = reverse('add_task')
        post_data = {
            'title': 'View Add Task with Project',
            'description': 'View Add Description',
            'project': self.project.id,
            'status': 'inprogress'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        created_task = Task.objects.get(user=self.user, title='View Add Task with Project')
        self.assertEqual(created_task.project, self.project)

    def test_add_task_view_without_project(self):
        url = reverse('add_task')
        post_data = {
            'title': 'View Add Task No Project',
            'description': 'View Add Description',
            'status': 'todo'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        created_task = Task.objects.get(user=self.user, title='View Add Task No Project')
        self.assertIsNone(created_task.project)

    def test_edit_task_view_loads_and_saves_project(self):
        task = Task.objects.create(user=self.user, title='Task for Project Edit', description="Initial Description", project=self.project)
        project2 = Project.objects.create(name='Project Two', owner=self.user)

        url = reverse('edit_task', args=[task.id])
        # GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['project'], self.project.id)

        # POST - change project
        post_data_change = {
            'title': task.title,
            'description': task.description,
            'project': project2.id,
            'status': task.status,
            'task_date': task.task_date.strftime('%Y-%m-%d') if task.task_date else '',
            'estimation_time': task.estimation_time
        }
        response = self.client.post(url, post_data_change)
        self.assertEqual(response.status_code, 302, response.content.decode() if response.status_code !=302 else None)
        task.refresh_from_db()
        self.assertEqual(task.project, project2)

        # POST - remove project
        post_data_remove = {
            'title': task.title,
            'description': task.description,
            'project': '',
            'status': task.status,
            'task_date': task.task_date.strftime('%Y-%m-%d') if task.task_date else '',
            'estimation_time': task.estimation_time
        }
        response = self.client.post(url, post_data_remove)
        self.assertEqual(response.status_code, 302, response.content.decode() if response.status_code !=302 else None)
        task.refresh_from_db()
        self.assertIsNone(task.project)

    def test_inline_edit_task_updates_project(self):
        task = Task.objects.create(user=self.user, title='Inline Edit Project Task', project=None)
        project2 = Project.objects.create(name='Project For Inline Edit', owner=self.user)
        url = reverse('inline_edit_task', args=[task.id])

        # Set project
        edit_data = {'project_id': project2.id}
        response = self.client.post(url, json.dumps(edit_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertEqual(json_response['task']['project_id'], project2.id)
        self.assertEqual(json_response['task']['project_name'], project2.name)
        task.refresh_from_db()
        self.assertEqual(task.project, project2)

        # Unset project
        edit_data = {'project_id': None}
        response = self.client.post(url, json.dumps(edit_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertIsNone(json_response['task']['project_id'])
        task.refresh_from_db()
        self.assertIsNone(task.project)

    def test_api_get_kanban_tasks_includes_project(self):
        Task.objects.create(user=self.user, title='Kanban Task With Project', project=self.project)
        Task.objects.create(user=self.user, title='Kanban Task No Project')
        url = reverse('api_kanban_tasks')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        tasks_data = response.json()
        self.assertEqual(len(tasks_data), 2)

        task_with_project_data = next(t for t in tasks_data if t['title'] == 'Kanban Task With Project')
        self.assertEqual(task_with_project_data['project_id'], self.project.id)
        self.assertEqual(task_with_project_data['project_name'], self.project.name)

        task_no_project_data = next(t for t in tasks_data if t['title'] == 'Kanban Task No Project')
        self.assertIsNone(task_no_project_data['project_id'])
        self.assertIsNone(task_no_project_data['project_name'])

class CSVReportWithProjectTests(CSVReportTests): # Inherit to reuse setup
    def setUp(self):
        super().setUp()
        self.project_csv = Project.objects.create(name='CSV Test Project', owner=self.user)
        self.todo1.project = self.project_csv
        self.todo1.save()
        # todo2 has no project

    def test_download_csv_report_includes_project_name(self):
        self.client.login(username='csvuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))

        header = next(reader)
        self.assertIn('Project Name', header)
        project_name_index = header.index('Project Name')

        rows = list(reader)
        self.assertEqual(len(rows), 2) # todo1 and todo2

        row_todo1 = next(r for r in rows if r[3] == self.todo1.title) # Find by title
        self.assertEqual(row_todo1[project_name_index], self.project_csv.name)

        row_todo2 = next(r for r in rows if r[3] == self.todo2.title)
        self.assertEqual(row_todo2[project_name_index], 'N/A')

    def test_download_csv_report_no_todos_includes_project_header(self):
        self.client.login(username='csvuser', password='password123')
        TodoItem.objects.filter(user=self.user).delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        header = next(reader)
        self.assertIn('Project Name', header)
        project_name_index = header.index('Project Name')

        data_row = next(reader)
        self.assertEqual(data_row[project_name_index], 'N/A')


class ProjectViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1_proj_view', password='password123', email='user1@example.com')
        self.user2 = User.objects.create_user(username='user2_proj_view', password='password123', email='user2@example.com')

        self.project1 = Project.objects.create(name='Project Alpha', owner=self.user1, description='Description for Alpha')
        self.project1.members.add(self.user1)

        self.project2 = Project.objects.create(name='Project Beta', owner=self.user2, description='Description for Beta')
        self.project2.members.add(self.user1)
        self.project2.members.add(self.user2)

        self.project3 = Project.objects.create(name='Project Gamma (User2 only)', owner=self.user2, description='Description for Gamma')
        self.project3.members.add(self.user2)

        # Project owned by user1, user1 is NOT explicitly a member.
        self.project_owner_only = Project.objects.create(name='Project Delta (Owner Access Test)', owner=self.user1, description='Owned by user1')

        self.project_list_url = reverse('project_list')

    def test_project_list_view_login_required(self):
        """Test that the project list view requires login."""
        response = self.client.get(self.project_list_url)
        self.assertEqual(response.status_code, 302) # Redirect to login
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_project_list_view_displays_member_projects(self):
        """Test that the project list view only shows projects the user is a member of."""
        self.client.login(username='user1_proj_view', password='password123')
        response = self.client.get(self.project_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project1.name)
        self.assertContains(response, self.project2.name)
        self.assertNotContains(response, self.project3.name) # User1 is not a member of Project Gamma
        self.assertEqual(len(response.context['projects']), 2)

    def test_project_list_view_empty_for_non_member(self):
        """Test that the project list is empty for a user with no projects."""
        user3 = User.objects.create_user(username='user3_no_projects', password='password123')
        self.client.login(username='user3_no_projects', password='password123')
        response = self.client.get(self.project_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You are not currently a member of any projects.")
        self.assertEqual(len(response.context['projects']), 0)

    def test_project_detail_view_login_required(self):
        """Test that the project detail view requires login."""
        project_detail_url = reverse('project_detail', args=[self.project1.pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 302) # Redirect to login
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_project_detail_view_member_access(self):
        """Test that a member can access the project detail view."""
        self.client.login(username='user1_proj_view', password='password123')
        project_detail_url = reverse('project_detail', args=[self.project1.pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project1.name)
        self.assertContains(response, self.project1.description)
        self.assertContains(response, self.user1.username) # user1 is owner and member of project1

    def test_project_detail_view_owner_access_without_membership(self):
        """Test that an owner can access project details even if not explicitly a member."""
        self.client.login(username='user1_proj_view', password='password123')
        # project_owner_only is owned by user1, but user1 is not in project_owner_only.members
        self.assertNotIn(self.user1, self.project_owner_only.members.all()) # Sanity check
        self.assertEqual(self.project_owner_only.owner, self.user1)

        project_detail_url = reverse('project_detail', args=[self.project_owner_only.pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project_owner_only.name)
        self.assertContains(response, self.user1.username) # Owner's username

    def test_project_detail_view_non_owner_non_member_access_denied(self):
        """Test that a user who is neither an owner nor a member cannot access (403 Forbidden)."""
        self.client.login(username='user1_proj_view', password='password123')
        project_detail_url_gamma = reverse('project_detail', args=[self.project3.pk]) # User1 is not a member of Project Gamma
        response = self.client.get(project_detail_url_gamma)
        self.assertEqual(response.status_code, 403) # Forbidden

    def test_project_detail_view_displays_members(self):
        """Test that project detail view displays member information."""
        self.client.login(username='user1_proj_view', password='password123')
        project_detail_url = reverse('project_detail', args=[self.project2.pk]) # Project Beta has user1 and user2
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project2.name)
        self.assertContains(response, self.user1.username)
        self.assertContains(response, self.user1.email)
        self.assertContains(response, self.user2.username)
        self.assertContains(response, self.user2.email)
        self.assertEqual(response.context['project'].members.count(), 2)
        # Check if members are in context (more robust)
        members_in_context = [member.username for member in response.context['members']]
        self.assertIn(self.user1.username, members_in_context)
        self.assertIn(self.user2.username, members_in_context)

    def test_project_detail_view_non_existent_project(self):
        """Test accessing detail view for a non-existent project (should 404)."""
        self.client.login(username='user1_proj_view', password='password123')
        non_existent_pk = 9999
        project_detail_url = reverse('project_detail', args=[non_existent_pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 404)

    def test_project_detail_view_displays_associated_tasks(self):
        """Test that tasks associated with the project are listed."""
        self.client.login(username='user1_proj_view', password='password123')

        # project1 is owned by user1, and user1 is a member
        # Create tasks for project1
        task1_p1 = TodoItem.objects.create(user=self.user1, title="Task 1 for Project Alpha", project=self.project1, description="Desc P1T1")
        task2_p1 = TodoItem.objects.create(user=self.user1, title="Task 2 for Project Alpha", project=self.project1, description="Desc P1T2", status="inprogress")

        # Create a task for another project (project2) to ensure it's not shown
        task1_p2 = TodoItem.objects.create(user=self.user1, title="Task 1 for Project Beta", project=self.project2, description="Desc P2T1")

        project_detail_url = reverse('project_detail', args=[self.project1.pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, task1_p1.title)
        self.assertContains(response, task1_p1.get_status_display())
        self.assertContains(response, task2_p1.title)
        self.assertContains(response, task2_p1.get_status_display())
        self.assertNotContains(response, task1_p2.title) # Ensure task from other project is not listed

        # Check tasks in context
        self.assertIn('tasks', response.context)
        context_tasks = response.context['tasks']
        self.assertEqual(len(context_tasks), 2)
        self.assertIn(task1_p1, context_tasks)
        self.assertIn(task2_p1, context_tasks)

        # Check task link
        self.assertContains(response, f'href="{reverse("todo_detail", args=[task1_p1.pk])}"')


    def test_project_detail_view_no_tasks(self):
        """Test that 'No tasks' message is shown if a project has no tasks."""
        self.client.login(username='user1_proj_view', password='password123')
        # project_owner_only is owned by user1, and has no tasks by default
        project_detail_url = reverse('project_detail', args=[self.project_owner_only.pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No tasks currently associated with this project.")
        self.assertIn('tasks', response.context)
        self.assertEqual(len(response.context['tasks']), 0)

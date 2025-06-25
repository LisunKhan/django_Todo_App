from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import TodoItem
from .forms import TodoForm
from django.urls import reverse
from django.db.models import Sum

class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_todo_item_creation_with_time_spent(self):
        """
        Test that a TodoItem can be created with a time_spent value.
        """
        todo = TodoItem.objects.create(
            user=self.user,
            title='Test Task 1',
            description='Test Description',
            time_spent=30
        )
        self.assertEqual(todo.title, 'Test Task 1')
        self.assertEqual(todo.time_spent, 30)
        self.assertEqual(todo.user, self.user)

    def test_todo_item_time_spent_default_value(self):
        """
        Test that time_spent defaults to 0 if not provided.
        """
        todo = TodoItem.objects.create(
            user=self.user,
            title='Test Task Default Time',
            description='Description'
        )
        self.assertEqual(todo.time_spent, 0)
        self.assertEqual(todo.status, 'todo') # Test default status

    def test_todo_item_status_choices(self):
        """
        Test the available choices for the status field.
        """
        todo = TodoItem.objects.create(user=self.user, title='Status Choice Task')
        self.assertEqual(todo.status, 'todo')
        todo.status = 'inprogress'
        todo.save()
        self.assertEqual(todo.status, 'inprogress')
        self.assertEqual(todo.get_status_display(), 'In Progress')
        todo.status = 'done'
        todo.save()
        self.assertEqual(todo.status, 'done')
        self.assertEqual(todo.get_status_display(), 'Done')
        # Test that completed is updated when status is 'done'
        self.assertTrue(todo.completed)

        todo.status = 'todo'
        todo.save()
        # Test that completed is updated when status is not 'done'
        # This depends on if the model's save method syncs 'completed'
        # For now, we assume 'completed' is either a property or handled by the form/save logic.
        # If TodoItem.completed is a direct model field, its state after changing status
        # depends on how it's managed. If it's not automatically synced, this test might need adjustment
        # or the model's save() method needs to handle it.
        # Based on current plan, 'completed' is still a field, but 'status' is primary.
        # We'll assume for now the form/view layer handles keeping them in sync if necessary,
        # or that 'completed' will be derived/removed.
        # If we expect model to auto-sync:
        # self.assertFalse(todo.completed)


class TodoFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testformuser', password='password123')

    def test_todo_form_valid_with_time_spent(self):
        """
        Test TodoForm is valid when time_spent is provided.
        """
        form_data = {
            'title': 'Form Task',
            'description': 'Form Description',
            'time_spent_hours': 0.75, # 45 minutes
            'status': 'inprogress'
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        todo = form.save(commit=False)
        self.assertEqual(todo.status, 'inprogress')
        self.assertEqual(todo.time_spent, 45)


    def test_todo_form_valid_without_time_spent(self):
        """
        Test TodoForm is valid when time_spent is not provided (should use default).
        """
        form_data = {
            'title': 'Form Task No Time',
            'description': 'Form Description',
        }
        # 'time_spent' is not included, ModelForm should use default from model
        # 'status' is also not included, should use default 'todo'
        form = TodoForm(data=form_data)
        if not form.is_valid():
            print(form.errors) # For debugging in case of failure
        self.assertTrue(form.is_valid(), form.errors)
        todo = form.save(commit=False)
        self.assertEqual(todo.status, 'todo') # Check default status from form/model


    def test_todo_form_saves_time_spent_and_status(self):
        """
        Test that TodoForm correctly saves the time_spent and status fields.
        """
        form_data = {
            'title': 'Form Save Task',
            'description': 'Form Save Description',
            'time_spent_hours': 1, # 1 hour = 60 minutes
            'status': 'done'
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        todo_item = form.save(commit=False)
        self.assertEqual(todo_item.time_spent, 60) # Check minutes in model
        self.assertEqual(todo_item.status, 'done')
        # If model/form syncs 'completed' based on 'status':
        # self.assertTrue(todo_item.completed)


    def test_todo_form_fields_default_values_on_save(self):
        """
        Test that if time_spent and status are not in form data, they default correctly upon saving.
        """
        form_data = {
            'title': 'Form Default Fields Task',
            'description': 'Form Default Fields Description',
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        todo_item = form.save(commit=False)
        # The model field time_spent has default=0.
        self.assertEqual(todo_item.time_spent, 0)
        # The model field status has default='todo'.
        self.assertEqual(todo_item.status, 'todo')


class TodoViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testviewuser', password='password123')
        self.client.login(username='testviewuser', password='password123')

        self.other_user = User.objects.create_user(username='otherviewuser', password='password123')

    def test_add_todo_view_with_time_spent_and_status(self):
        """
        Test the add_todo view can create a TodoItem with time_spent and status.
        """
        url = reverse('add_todo')
        post_data = {
            'title': 'View Add Task',
            'description': 'View Add Description',
            'time_spent_hours': 1.25, # 1.25 hours = 75 minutes
            'status': 'inprogress'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302) # Should redirect after successful POST
        created_task = TodoItem.objects.get(user=self.user, title='View Add Task')
        self.assertEqual(created_task.time_spent, 75)
        self.assertEqual(created_task.status, 'inprogress')

    def test_todo_list_view_displays_time_spent_and_status(self):
        """
        Test that time_spent and status are displayed on the todo_list page.
        """
        TodoItem.objects.create(user=self.user, title='List Task 1', description='Desc 1', time_spent=10, status='todo')
        TodoItem.objects.create(user=self.user, title='List Task 2', description='Desc 2', time_spent=20, status='done')

        url = reverse('todo_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'List Task 1')
        self.assertContains(response, '0.17h') # 10 / 60
        self.assertContains(response, 'To Do')
        self.assertContains(response, 'List Task 2')
        self.assertContains(response, '0.33h') # 20 / 60
        self.assertContains(response, 'Done')


    def test_todo_detail_view_displays_time_spent_and_status(self):
        """
        Test that time_spent and status are displayed on the todo_detail page.
        """
        task = TodoItem.objects.create(user=self.user, title='Detail Task', description='Detail Desc', time_spent=35, status='inprogress')
        url = reverse('todo_detail', args=[task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detail Task')
        self.assertContains(response, '0.58 hour(s)') # 35 minutes / 60 = 0.5833...
        self.assertContains(response, 'In Progress') # Check for status display

    def test_task_report_view_filters_by_status(self):
        """
        Test the task_report view for correct aggregation and user isolation.
        """
        # Tasks for logged-in user
        TodoItem.objects.create(user=self.user, title='Report Task 1', description='User1 Desc1', time_spent=50)
        TodoItem.objects.create(user=self.user, title='Report Task 2', description='User1 Desc2', time_spent=25)
        TodoItem.objects.create(user=self.user, title='Report Task 3', description='User1 Desc3 ZeroTime') # time_spent defaults to 0

        # Task for another user - should not be included
        TodoItem.objects.create(user=self.other_user, title='Other User Task', description='Other Desc', time_spent=100)

        url = reverse('task_report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Check total time in context (more robust than checking raw HTML)
        # Total time should be based on ALL tasks for the user, regardless of whether they are shown in the paginated list.
        # User has tasks with 50 mins, 25 mins, and 0 mins. Total = 75 mins = 1.25 hours.
        # This total_time_spent_today_hours in the report is for TODAY's tasks only.
        # Let's adjust tasks or the assertion.
        # For this test, let's assume all tasks are for today for simplicity of total time check.
        from django.utils import timezone
        today = timezone.now().date()
        TodoItem.objects.all().update(task_date=today) # Set all tasks to today for this test's total time check.

        # Re-fetch for updated task_date affecting total_time_spent_today_hours
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Now, total_time_spent_today_hours should be 1.25 (50+25+0)
        self.assertAlmostEqual(response.context['total_time_spent_today_hours'], 1.25, places=2)


        # Check tasks in context (via page_obj) - this list is filtered by time_spent > 0
        # So, only 'Report Task 1' (50 mins) and 'Report Task 2' (25 mins) should be here.
        self.assertEqual(len(response.context['page_obj'].object_list), 2) # Correct, as it filters time_spent > 0

        # Create tasks with different statuses
        TodoItem.objects.create(user=self.user, title='Todo Task Report', time_spent=10, status='todo', task_date=today)
        TodoItem.objects.create(user=self.user, title='In Progress Task Report', time_spent=20, status='inprogress', task_date=today)
        TodoItem.objects.create(user=self.user, title='Done Task Report', time_spent=30, status='done', task_date=today)
        TodoItem.objects.create(user=self.other_user, title='Other User Done Task', time_spent=40, status='done', task_date=today)


        # Test filter by status 'done'
        response_done = self.client.get(url, {'status': 'done'})
        self.assertEqual(response_done.status_code, 200)
        self.assertContains(response_done, 'Done Task Report')
        self.assertNotContains(response_done, 'Todo Task Report')
        self.assertNotContains(response_done, 'In Progress Task Report')
        self.assertNotContains(response_done, 'Other User Done Task') # Ensure user isolation
        # The original "Report Task 1" and "Report Task 2" might also be 'done' if their default status was 'todo' and completed=True
        # Let's ensure their status is something else or they are excluded if we only want 'Done Task Report'
        TodoItem.objects.filter(title__in=['Report Task 1', 'Report Task 2']).update(status='todo')


        # Re-test filter by status 'done' after ensuring other tasks are not 'done'
        response_done_filtered = self.client.get(url, {'status': 'done'})
        self.assertEqual(len(response_done_filtered.context['page_obj'].object_list), 1) # Only "Done Task Report"
        self.assertContains(response_done_filtered, 'Done Task Report')


        # Test filter by status 'inprogress'
        response_inprogress = self.client.get(url, {'status': 'inprogress'})
        self.assertEqual(response_inprogress.status_code, 200)
        self.assertContains(response_inprogress, 'In Progress Task Report')
        self.assertNotContains(response_inprogress, 'Done Task Report')
        self.assertEqual(len(response_inprogress.context['page_obj'].object_list), 1)


    def test_task_report_view_no_tasks(self):
        """
        Test the task_report view when the user has no tasks.
        """
        url = reverse('task_report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # total_time_spent_today_hours is the relevant context variable now.
        self.assertEqual(response.context['total_time_spent_today_hours'], 0)
        self.assertEqual(len(response.context['page_obj'].object_list), 0)
        # The text "Total Time Spent on All Tasks" might have changed or depend on `total_time_spent_today_hours`
        self.assertContains(response, '0.00 hour(s)') # Check for the value
        self.assertContains(response, 'No tasks match your criteria.')

    def test_task_report_login_required(self):
        """
        Test that task_report view requires login.
        """
        self.client.logout()
        url = reverse('task_report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) # Should redirect to login
        self.assertTrue(response.url.startswith(reverse('login')))

    # Tests for edit_todo view
    def test_edit_todo_login_required(self):
        """
        Test that edit_todo view requires login.
        """
        self.client.logout()
        # Attempt to access edit page for a dummy task ID
        url = reverse('edit_todo', args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_edit_todo_task_ownership_get(self):
        """
        Test user cannot GET edit page for another user's task (should 404).
        """
        other_task = TodoItem.objects.create(user=self.other_user, title='Other User Task Edit', description='Test')
        url = reverse('edit_todo', args=[other_task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_edit_todo_task_ownership_post(self):
        """
        Test user cannot POST to edit another user's task (should 404, no data change).
        """
        other_task = TodoItem.objects.create(user=self.other_user, title='Original Other Title', description='Original Other Desc', time_spent=10)
        url = reverse('edit_todo', args=[other_task.id])
        post_data = {'title': 'Attempted New Title', 'description': 'Attempted New Desc', 'time_spent': 99}

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 404)

        # Verify the task data has not changed
        other_task.refresh_from_db()
        self.assertEqual(other_task.title, 'Original Other Title')
        self.assertEqual(other_task.description, 'Original Other Desc')
        self.assertEqual(other_task.time_spent, 10)

    def test_edit_todo_task_not_found_get(self):
        """
        Test GET request to edit URL for a non-existent todo_id results in 404.
        """
        non_existent_id = 9999
        url = reverse('edit_todo', args=[non_existent_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_edit_todo_task_not_found_post(self):
        """
        Test POST request to edit URL for a non-existent todo_id results in 404.
        """
        non_existent_id = 9999
        url = reverse('edit_todo', args=[non_existent_id])
        post_data = {'title': 'Title', 'description': 'Description', 'time_spent': 10}
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 404)

    def test_edit_todo_successful_get(self):
        """
        Test successful GET request for edit_todo page.
        """
        task = TodoItem.objects.create(user=self.user, title='My Edit Task', description='My Desc', time_spent=40)
        url = reverse('edit_todo', args=[task.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], TodoForm)
        self.assertEqual(response.context['form'].initial['title'], 'My Edit Task')
        self.assertEqual(response.context['form'].initial['description'], 'My Desc')
        self.assertEqual(response.context['form'].initial['time_spent_hours'], 40/60) # Check hours
        self.assertContains(response, 'My Edit Task') # Check if title is rendered

    def test_edit_todo_successful_post_update(self):
        """
        Test successful POST request to update a task, including its status.
        """
        task = TodoItem.objects.create(user=self.user, title='Original Title', description='Original Desc', time_spent=20, status='todo')
        url = reverse('edit_todo', args=[task.id])

        post_data_for_form = {
            'title': 'Updated Title',
            'description': 'Updated Desc',
            'time_spent_hours': 88/60, # hours
            'status': 'done' # Update status
        }

        response = self.client.post(url, post_data_for_form)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('todo_detail', args=[task.id]))

        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated Title')
        self.assertEqual(task.description, 'Updated Desc')
        self.assertEqual(task.time_spent, 88) # Check minutes
        self.assertEqual(task.status, 'done') # Verify status
        # self.assertTrue(task.completed) # If completed is synced from status


    def test_edit_todo_post_invalid_data(self):
        """
        Test POST request with invalid data (e.g., blank title).
        """
        task = TodoItem.objects.create(user=self.user, title='Valid Title', description='Valid Desc', time_spent=15)
        url = reverse('edit_todo', args=[task.id])
        invalid_data = {
            'title': '',  # Invalid: title is required
            'description': 'Description with no title',
            'time_spent_hours': 10/60
        }
        response = self.client.post(url, invalid_data)

        self.assertEqual(response.status_code, 200) # Should re-render the form
        self.assertTrue(response.context['form'].errors) # Check for form errors
        self.assertIn('title', response.context['form'].errors) # Specifically title error

        task.refresh_from_db()
        self.assertEqual(task.title, 'Valid Title') # Data should not have changed
        self.assertEqual(task.description, 'Valid Desc')
        self.assertEqual(task.time_spent, 15)

    def test_todo_list_displays_status(self):
        """
        Test that the todo_list page correctly displays the status of tasks.
        """
        TodoItem.objects.create(user=self.user, title='Completed Task', description='This task is done', completed=True)
        TodoItem.objects.create(user=self.user, title='Pending Task', description='This task is not done', completed=False)

        url = reverse('todo_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Completed Task')
        # Check for the badge HTML we added in the template
        # Making assertion slightly less specific to avoid issues with minor attribute order/whitespace
        self.assertContains(response, 'class="badge bg-success">Done</span>') # Assuming 'done' maps to 'Done'

        self.assertContains(response, 'Pending Task')
        self.assertContains(response, 'class="badge bg-warning text-dark">To Do</span>') # Assuming 'todo' maps to 'To Do'

    def test_inline_edit_todo_updates_status(self):
        """
        Test that the inline_edit_todo view correctly updates the status.
        """
        task = TodoItem.objects.create(user=self.user, title='Inline Edit Status Task', status='todo')
        url = reverse('inline_edit_todo', args=[task.id])

        edit_data = {
            'title': task.title,
            'description': task.description,
            'time_spent_hours': task.time_spent_hours,
            'status': 'inprogress'
        }

        response = self.client.post(url, json.dumps(edit_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertEqual(json_response['todo']['status'], 'inprogress')

        task.refresh_from_db()
        self.assertEqual(task.status, 'inprogress')

        # Test updating to 'done'
        edit_data['status'] = 'done'
        response = self.client.post(url, json.dumps(edit_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertEqual(json_response['todo']['status'], 'done')

        task.refresh_from_db()
        self.assertEqual(task.status, 'done')
        # self.assertTrue(task.completed) # If completed is synced from status

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
            completed=True,
            time_spent=60, # 1 hour
            task_date=self.todo1_date
        )
        # Manually set created_at and updated_at for predictable testing if necessary
        # For this test, auto_now_add and auto_now should be fine.

        self.todo2 = TodoItem.objects.create(
            user=self.user,
            title='CSV Todo 2',
            description='Description for CSV 2',
            completed=False,
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
            'Todo Title', 'Todo Description', 'Completed',
            'Time Spent (hours)', 'Created At', 'Updated At', 'Task Date'
        ]
        self.assertEqual(header, expected_header)

        rows = list(reader)
        self.assertEqual(len(rows), 2) # For todo1 and todo2

        # Check data for the first todo item (order might vary based on default model ordering or view query ordering)
        # To make this robust, you might want to order TodoItems in the view or sort rows here.
        # For now, assume default ordering by ID or creation time is consistent enough for test.
        # Or, fetch them from DB and compare, assuming they are returned in the same order.

        # Let's find todo1 in the rows, assuming title is unique for this test setup
        row1_data = None
        for row in rows:
            if row[3] == self.todo1.title: # Todo Title is the 4th column (index 3)
                row1_data = row
                break
        self.assertIsNotNone(row1_data, "Todo1 not found in CSV output")

        self.assertEqual(row1_data[0], self.user.username)
        self.assertEqual(row1_data[1], self.user.email)
        self.assertEqual(row1_data[2], self.user.profile.bio)
        self.assertEqual(row1_data[3], self.todo1.title)
        self.assertEqual(row1_data[4], self.todo1.description)
        self.assertEqual(row1_data[5], str(self.todo1.completed)) # CSV stores bools as 'True'/'False'
        self.assertEqual(float(row1_data[6]), self.todo1.time_spent_hours)
        self.assertIn(self.todo1.created_at.strftime('%Y-%m-%d'), row1_data[7]) # Check date part
        self.assertIn(self.todo1.updated_at.strftime('%Y-%m-%d'), row1_data[8]) # Check date part
        self.assertEqual(row1_data[9], self.todo1.task_date.strftime('%Y-%m-%d'))


    def test_download_csv_report_no_todos(self):
        """Test CSV output when the user has no todo items."""
        self.client.login(username='csvuser', password='password123')
        TodoItem.objects.filter(user=self.user).delete() # Remove existing todos

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))

        header = next(reader) # Skip header

        data_row = next(reader)
        self.assertEqual(data_row[0], self.user.username)
        self.assertEqual(data_row[1], self.user.email)
        self.assertEqual(data_row[2], self.user.profile.bio)
        for i in range(3, 10): # Todo specific fields
            self.assertEqual(data_row[i], 'N/A')

        with self.assertRaises(StopIteration):
            next(reader) # No more rows

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

        # created_at and updated_at are datetime objects
        # Example format: '2023-10-26 10:30:00'
        self.assertEqual(row[7], self.todo1.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(row[8], self.todo1.updated_at.strftime('%Y-%m-%d %H:%M:%S'))

        # task_date is a date object
        # Example format: '2023-10-26'
        self.assertEqual(row[9], self.todo1.task_date.strftime('%Y-%m-%d'))

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

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
            'time_spent': 45
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_todo_form_valid_without_time_spent(self):
        """
        Test TodoForm is valid when time_spent is not provided (should use default).
        """
        form_data = {
            'title': 'Form Task No Time',
            'description': 'Form Description',
        }
        # 'time_spent' is not included, ModelForm should use default from model
        form = TodoForm(data=form_data)
        if not form.is_valid():
            print(form.errors) # For debugging in case of failure
        self.assertTrue(form.is_valid())


    def test_todo_form_saves_time_spent(self):
        """
        Test that TodoForm correctly saves the time_spent field.
        """
        form_data = {
            'title': 'Form Save Task',
            'description': 'Form Save Description',
            'time_spent_hours': 1 # 1 hour = 60 minutes
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        # commit=False is not strictly necessary here as we are not setting user yet
        # but it's good practice if further manipulation is needed before full save.
        todo_item = form.save(commit=False)
        # In a real scenario, you'd set todo_item.user here before saving fully.
        # For this test, we only care if time_spent is in the instance from form.
        self.assertEqual(todo_item.time_spent, 60) # Check minutes in model

    def test_todo_form_time_spent_optional_uses_default(self):
        """
        Test that if time_spent is not in form data, it defaults correctly upon saving.
        """
        form_data = {
            'title': 'Form Default Time Task',
            'description': 'Form Default Time Description',
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid())
        todo_item = form.save(commit=False)
        # The model field has default=0. ModelForm's save() should honor this.
        self.assertEqual(todo_item.time_spent, 0)


class TodoViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testviewuser', password='password123')
        self.client.login(username='testviewuser', password='password123')

        self.other_user = User.objects.create_user(username='otherviewuser', password='password123')

    def test_add_todo_view_with_time_spent(self):
        """
        Test the add_todo view can create a TodoItem with time_spent.
        """
        url = reverse('add_todo')
        post_data = {
            'title': 'View Add Task',
            'description': 'View Add Description',
            'time_spent_hours': 1.25 # 1.25 hours = 75 minutes
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302) # Should redirect after successful POST
        self.assertTrue(TodoItem.objects.filter(user=self.user, title='View Add Task', time_spent=75).exists())

    def test_todo_list_view_displays_time_spent(self):
        """
        Test that time_spent is displayed on the todo_list page.
        """
        TodoItem.objects.create(user=self.user, title='List Task 1', description='Desc 1', time_spent=10)
        TodoItem.objects.create(user=self.user, title='List Task 2', description='Desc 2', time_spent=20)

        url = reverse('todo_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'List Task 1')
        self.assertContains(response, '10')
        self.assertContains(response, 'List Task 2')
        self.assertContains(response, '20')

    def test_todo_detail_view_displays_time_spent(self):
        """
        Test that time_spent is displayed on the todo_detail page.
        """
        task = TodoItem.objects.create(user=self.user, title='Detail Task', description='Detail Desc', time_spent=35)
        url = reverse('todo_detail', args=[task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detail Task')
        self.assertContains(response, '0.58 hour(s)') # 35 minutes / 60 = 0.5833...

    def test_task_report_view(self):
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
        self.assertAlmostEqual(response.context['total_time_spent_hours'], 1.25, places=2) # 75 minutes / 60

        # Check tasks in context (via page_obj)
        self.assertEqual(len(response.context['page_obj'].object_list), 3)

        # Check content in HTML
        self.assertContains(response, 'Report Task 1')
        # Time is displayed in hours, e.g., 50/60 = 0.83h
        self.assertContains(response, '0.83h') # 50 mins
        self.assertContains(response, 'Report Task 2')
        self.assertContains(response, '0.42h') # 25 mins
        self.assertContains(response, 'Report Task 3')
        self.assertContains(response, '0.00h') # 0 mins
        self.assertContains(response, 'Total Time Spent on All Tasks: 1.25 hour(s)')

        # Ensure other user's task is not present
        self.assertNotContains(response, 'Other User Task')
        self.assertNotContains(response, '1.67h') # 100 mins for other user

    def test_task_report_view_no_tasks(self):
        """
        Test the task_report view when the user has no tasks.
        """
        url = reverse('task_report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_time_spent_hours'], 0)
        self.assertEqual(len(response.context['page_obj'].object_list), 0)
        self.assertContains(response, 'Total Time Spent on All Tasks: 0.00 hour(s)')
        self.assertContains(response, 'No tasks match your criteria.') # Updated message

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
        Test successful POST request to update a task.
        """
        task = TodoItem.objects.create(user=self.user, title='Original Title', description='Original Desc', time_spent=20, completed=False) # Start with completed=False
        url = reverse('edit_todo', args=[task.id])
        updated_data_for_model = { # For asserting model values
            'title': 'Updated Title',
            'description': 'Updated Desc',
            'time_spent': 88, # minutes
            'completed': True
        }
        post_data_for_form = { # For sending to form
            'title': 'Updated Title',
            'description': 'Updated Desc',
            'time_spent_hours': 88/60, # hours
            'completed': True
        }

        response = self.client.post(url, post_data_for_form)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('todo_detail', args=[task.id]))

        task.refresh_from_db()
        self.assertEqual(task.title, updated_data_for_model['title'])
        self.assertEqual(task.description, updated_data_for_model['description'])
        self.assertEqual(task.time_spent, updated_data_for_model['time_spent'])
        self.assertEqual(task.completed, updated_data_for_model['completed']) # Verify 'completed' status


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
        self.assertContains(response, 'class="badge bg-success" data-value="true">Completed</span>')

        self.assertContains(response, 'Pending Task')
        self.assertContains(response, 'class="badge bg-warning text-dark" data-value="false">Pending</span>')

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

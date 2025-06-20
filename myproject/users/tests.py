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
            'time_spent': 60
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid())
        # commit=False is not strictly necessary here as we are not setting user yet
        # but it's good practice if further manipulation is needed before full save.
        todo_item = form.save(commit=False)
        # In a real scenario, you'd set todo_item.user here before saving fully.
        # For this test, we only care if time_spent is in the instance from form.
        self.assertEqual(todo_item.time_spent, 60)

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
            'time_spent': 75
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
        self.assertContains(response, '35')

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
        self.assertEqual(response.context['total_time_spent'], 75) # 50 + 25 + 0

        # Check tasks in context
        self.assertEqual(len(response.context['tasks']), 3)

        # Check content in HTML
        self.assertContains(response, 'Report Task 1')
        self.assertContains(response, '50')
        self.assertContains(response, 'Report Task 2')
        self.assertContains(response, '25')
        self.assertContains(response, 'Report Task 3')
        self.assertContains(response, '0') # Default time_spent
        self.assertContains(response, 'Total Time Spent on All Tasks: 75')

        # Ensure other user's task is not present
        self.assertNotContains(response, 'Other User Task')
        self.assertNotContains(response, '100')

    def test_task_report_view_no_tasks(self):
        """
        Test the task_report view when the user has no tasks.
        """
        url = reverse('task_report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_time_spent'], 0)
        self.assertEqual(len(response.context['tasks']), 0)
        self.assertContains(response, 'Total Time Spent on All Tasks: 0')
        self.assertContains(response, 'No tasks found.')

    def test_task_report_login_required(self):
        """
        Test that task_report view requires login.
        """
        self.client.logout()
        url = reverse('task_report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) # Should redirect to login
        self.assertTrue(response.url.startswith(reverse('login')))

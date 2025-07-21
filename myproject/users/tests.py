from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import TodoItem, TodoLog, Project
from .forms import TodoForm, TodoLogForm
from django.urls import reverse
from django.db.models import Sum
import json
from datetime import date

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
        )
        TodoLog.objects.create(todo_item=todo, log_time=30)
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
        self.assertEqual(todo.status, 'todo')

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

        todo.status = 'todo'
        todo.save()

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
            'status': 'inprogress'
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        todo = form.save(commit=False)
        todo.user = self.user
        todo.save()
        TodoLog.objects.create(todo_item=todo, log_time=45)
        self.assertEqual(todo.status, 'inprogress')
        self.assertEqual(todo.time_spent, 45)


    def test_todo_form_valid_without_time_spent(self):
        """
        Test TodoForm is valid when time_spent is not provided (should use default).
        """
        form_data = {
            'title': 'Form Task No Time',
            'description': 'Form Description',
            'status': 'todo'
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        todo = form.save(commit=False)
        self.assertEqual(todo.status, 'todo')


    def test_todo_form_saves_time_spent_and_status(self):
        """
        Test that TodoForm correctly saves the time_spent and status fields.
        """
        form_data = {
            'title': 'Form Save Task',
            'description': 'Form Save Description',
            'status': 'done'
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        todo_item = form.save(commit=False)
        todo_item.user = self.user
        todo_item.save()
        TodoLog.objects.create(todo_item=todo_item, log_time=60)
        self.assertEqual(todo_item.time_spent, 60)
        self.assertEqual(todo_item.status, 'done')


    def test_todo_form_fields_default_values_on_save(self):
        """
        Test that if time_spent and status are not in form data, they default correctly upon saving.
        """
        form_data = {
            'title': 'Form Default Fields Task',
            'description': 'Form Default Fields Description',
            'status': 'todo'
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        todo_item = form.save(commit=False)
        self.assertEqual(todo_item.time_spent, 0)
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
            'status': 'inprogress'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        created_task = TodoItem.objects.get(user=self.user, title='View Add Task')
        TodoLog.objects.create(todo_item=created_task, log_time=75)
        self.assertEqual(created_task.time_spent, 75)
        self.assertEqual(created_task.status, 'inprogress')

    def test_todo_list_view_displays_time_spent_and_status(self):
        """
        Test that time_spent and status are displayed on the todo_list page.
        """
        task1 = TodoItem.objects.create(user=self.user, title='List Task 1', description='Desc 1', status='todo')
        TodoLog.objects.create(todo_item=task1, log_time=10)
        task2 = TodoItem.objects.create(user=self.user, title='List Task 2', description='Desc 2', status='done')
        TodoLog.objects.create(todo_item=task2, log_time=20)

        url = reverse('todo_list')
        response = self.client.get(url, {'order_by': 'title'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'List Task 1')
        self.assertContains(response, '0.17')
        self.assertContains(response, 'To Do')
        self.assertContains(response, 'List Task 2')
        self.assertContains(response, '0.33')
        self.assertContains(response, 'Done')


    def test_todo_detail_view_displays_time_spent_and_status(self):
        """
        Test that time_spent and status are displayed on the todo_detail page.
        """
        task = TodoItem.objects.create(user=self.user, title='Detail Task', description='Detail Desc', status='inprogress')
        TodoLog.objects.create(todo_item=task, log_time=35)
        url = reverse('todo_detail', args=[task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detail Task')
        self.assertContains(response, '0.58')
        self.assertContains(response, 'In Progress')

    def test_task_report_view_filters_by_status(self):
        """
        Test the task_report view for correct aggregation and user isolation.
        """
        from django.utils import timezone
        today = timezone.now().date()

        task1 = TodoItem.objects.create(user=self.user, title='Report Task 1', description='User1 Desc1')
        TodoLog.objects.create(todo_item=task1, log_time=50, task_date=today)
        task2 = TodoItem.objects.create(user=self.user, title='Report Task 2', description='User1 Desc2')
        TodoLog.objects.create(todo_item=task2, log_time=25, task_date=today)
        TodoItem.objects.create(user=self.user, title='Report Task 3', description='User1 Desc3 ZeroTime')

        other_task = TodoItem.objects.create(user=self.other_user, title='Other User Task', description='Other Desc')
        TodoLog.objects.create(todo_item=other_task, log_time=100, task_date=today)

        url = reverse('task_report')
        response = self.client.get(url, {'order_by': 'title'})
        self.assertEqual(response.status_code, 200)

        self.assertAlmostEqual(response.context['total_time_spent_today_hours'], 1.25, places=2)
        self.assertEqual(len(response.context['page_obj'].object_list), 2)

        task_todo = TodoItem.objects.create(user=self.user, title='Todo Task Report', status='todo')
        TodoLog.objects.create(todo_item=task_todo, log_time=10, task_date=today)
        task_inprogress = TodoItem.objects.create(user=self.user, title='In Progress Task Report', status='inprogress')
        TodoLog.objects.create(todo_item=task_inprogress, log_time=20, task_date=today)
        task_done = TodoItem.objects.create(user=self.user, title='Done Task Report', status='done')
        TodoLog.objects.create(todo_item=task_done, log_time=30, task_date=today)
        other_task_done = TodoItem.objects.create(user=self.other_user, title='Other User Done Task', status='done')
        TodoLog.objects.create(todo_item=other_task_done, log_time=40, task_date=today)

        response_done = self.client.get(url, {'status': 'done', 'order_by': 'title'})
        self.assertEqual(response_done.status_code, 200)
        self.assertContains(response_done, 'Done Task Report')
        self.assertNotContains(response_done, 'Todo Task Report')
        self.assertNotContains(response_done, 'In Progress Task Report')
        self.assertNotContains(response_done, 'Other User Done Task')

        response_done_filtered = self.client.get(url, {'status': 'done', 'order_by': 'title'})
        self.assertEqual(len(response_done_filtered.context['page_obj'].object_list), 1)
        self.assertContains(response_done_filtered, 'Done Task Report')

        response_inprogress = self.client.get(url, {'status': 'inprogress', 'order_by': 'title'})
        self.assertEqual(response_inprogress.status_code, 200)
        self.assertContains(response_inprogress, 'In Progress Task Report')
        self.assertNotContains(response_inprogress, 'Done Task Report')
        self.assertEqual(len(response_inprogress.context['page_obj'].object_list), 1)


    def test_task_report_view_no_tasks(self):
        """
        Test the task_report view when the user has no tasks.
        """
        url = reverse('task_report')
        response = self.client.get(url, {'order_by': 'title'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_time_spent_today_hours'], 0)
        self.assertEqual(len(response.context['page_obj'].object_list), 0)
        self.assertContains(response, '0.00')
        self.assertContains(response, 'No tasks match your criteria.')

    def test_task_report_login_required(self):
        """
        Test that task_report view requires login.
        """
        self.client.logout()
        url = reverse('task_report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_edit_todo_login_required(self):
        """
        Test that edit_todo view requires login.
        """
        self.client.logout()
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
        other_task = TodoItem.objects.create(user=self.other_user, title='Original Other Title', description='Original Other Desc')
        TodoLog.objects.create(todo_item=other_task, log_time=10)
        url = reverse('edit_todo', args=[other_task.id])
        post_data = {'title': 'Attempted New Title', 'description': 'Attempted New Desc'}

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 404)

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
        post_data = {'title': 'Title', 'description': 'Description'}
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 404)

    def test_edit_todo_successful_get(self):
        """
        Test successful GET request for edit_todo page.
        """
        task = TodoItem.objects.create(user=self.user, title='My Edit Task', description='My Desc')
        TodoLog.objects.create(todo_item=task, log_time=40)
        url = reverse('edit_todo', args=[task.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], TodoForm)
        self.assertEqual(response.context['form'].initial['title'], 'My Edit Task')
        self.assertEqual(response.context['form'].initial['description'], 'My Desc')
        self.assertContains(response, 'My Edit Task')

    def test_edit_todo_successful_post_update(self):
        """
        Test successful POST request to update a task, including its status.
        """
        task = TodoItem.objects.create(user=self.user, title='Original Title', description='Original Desc', status='todo')
        TodoLog.objects.create(todo_item=task, log_time=20)
        url = reverse('edit_todo', args=[task.id])

        post_data_for_form = {
            'title': 'Updated Title',
            'description': 'Updated Desc',
            'status': 'done'
        }

        response = self.client.post(url, post_data_for_form)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('todo_detail', args=[task.id]))

        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated Title')
        self.assertEqual(task.description, 'Updated Desc')
        self.assertEqual(task.status, 'done')


    def test_edit_todo_post_invalid_data(self):
        """
        Test POST request with invalid data (e.g., blank title).
        """
        task = TodoItem.objects.create(user=self.user, title='Valid Title', description='Valid Desc')
        TodoLog.objects.create(todo_item=task, log_time=15)
        url = reverse('edit_todo', args=[task.id])
        invalid_data = {
            'title': '',
            'description': 'Description with no title',
        }
        response = self.client.post(url, invalid_data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertIn('title', response.context['form'].errors)

        task.refresh_from_db()
        self.assertEqual(task.title, 'Valid Title')
        self.assertEqual(task.description, 'Valid Desc')
        self.assertEqual(task.time_spent, 15)

    def test_todo_list_displays_status(self):
        """
        Test that the todo_list page correctly displays the status of tasks.
        """
        TodoItem.objects.create(user=self.user, title='Completed Task', description='This task is done', status='done')
        TodoItem.objects.create(user=self.user, title='Pending Task', description='This task is not done', status='todo')

        url = reverse('todo_list')
        response = self.client.get(url, {'order_by': 'title'})
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Completed Task')
        self.assertContains(response, 'class="badge bg-success">Done</span>')

        self.assertContains(response, 'Pending Task')
        self.assertContains(response, 'class="badge bg-warning text-dark">To Do</span>')

    def test_inline_edit_todo_updates_status(self):
        """
        Test that the inline_edit_todo view correctly updates the status.
        """
        task = TodoItem.objects.create(user=self.user, title='Inline Edit Status Task', status='todo')
        url = reverse('inline_edit_todo', args=[task.id])

        edit_data = {
            'title': task.title,
            'description': task.description,
            'status': 'inprogress'
        }

        response = self.client.post(url, json.dumps(edit_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertEqual(json_response['todo']['status'], 'inprogress')

        task.refresh_from_db()
        self.assertEqual(task.status, 'inprogress')

        edit_data['status'] = 'done'
        response = self.client.post(url, json.dumps(edit_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertEqual(json_response['todo']['status'], 'done')

        task.refresh_from_db()
        self.assertEqual(task.status, 'done')

from django.core.files.uploadedfile import SimpleUploadedFile
from .models import UserProfile

class UserProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='profileuser', password='password123', email='profile@example.com')
        self.client.login(username='profileuser', password='password123')

    def test_profile_created_on_user_creation(self):
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)
        self.assertEqual(self.user.profile.user, self.user)

    def test_profile_view_displays_information(self):
        self.user.profile.bio = "This is a test bio."
        self.user.profile.save()

        url = reverse('profile_view')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.email)
        self.assertContains(response, "This is a test bio.")
        self.assertContains(response, 'https://via.placeholder.com/150')

    def test_profile_view_login_required(self):
        self.client.logout()
        url = reverse('profile_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_edit_profile_view_get(self):
        self.user.profile.bio = "Initial bio for editing."
        self.user.profile.save()

        url = reverse('edit_profile_view')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Initial bio for editing.")
        self.assertIsInstance(response.context['form'], self.client.get(url).context['form'].__class__)

    def test_edit_profile_view_post_update_bio(self):
        url = reverse('edit_profile_view')
        new_bio = "This is an updated bio."
        post_data = {'bio': new_bio}

        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile_view'))

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, new_bio)

    def test_edit_profile_view_post_update_profile_picture(self):
        url = reverse('edit_profile_view')

        image_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        image = SimpleUploadedFile("test_pic.gif", image_content, content_type="image/gif")

        post_data = {'profile_picture': image, 'bio': self.user.profile.bio or ''}

        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile_view'))

        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.profile_picture.name.startswith('profile_pics/test_pic'))

        if self.user.profile.profile_picture:
            self.user.profile.profile_picture.delete(save=False)

    def test_edit_profile_view_post_empty_data(self):
        url = reverse('edit_profile_view')
        initial_bio = self.user.profile.bio

        response = self.client.post(url, {'bio': ''})
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, '')

        self.user.profile.bio = None
        self.user.profile.save()

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, '')

    def test_edit_profile_login_required(self):
        self.client.logout()
        url = reverse('edit_profile_view')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

        response = self.client.post(url, {'bio': 'Attempted update'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

import csv
from io import StringIO
from django.utils import timezone

class CSVReportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='csvuser', password='password123', email='csv@example.com')
        self.user.profile.bio = "Test bio for CSV export."
        self.user.profile.save()

        self.todo1_date = timezone.now().date()
        self.todo2_date = timezone.now().date() - timezone.timedelta(days=1)

        self.todo1 = TodoItem.objects.create(
            user=self.user,
            title='CSV Todo 1',
            description='Description for CSV 1',
            status='done',
        )
        TodoLog.objects.create(todo_item=self.todo1, log_time=60, task_date=self.todo1_date)

        self.todo2 = TodoItem.objects.create(
            user=self.user,
            title='CSV Todo 2',
            description='Description for CSV 2',
            status='todo',
        )
        TodoLog.objects.create(todo_item=self.todo2, log_time=30, task_date=self.todo2_date)
        self.url = reverse('download_csv_report')

    def test_download_csv_report_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_download_csv_report_headers_and_structure(self):
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
            'Time Spent (hours)', 'Created At', 'Updated At'
        ]
        self.assertEqual(header, expected_header)

        rows = list(reader)
        self.assertEqual(len(rows), TodoItem.objects.filter(user=self.user, logs__isnull=False).distinct().count())

        row1_data = None
        for row_idx, row_content in enumerate(rows):
            if row_content[3] == self.todo1.title:
                row1_data = row_content
                break
        self.assertIsNotNone(row1_data, f"Todo1 (title: {self.todo1.title}) not found in CSV output. Rows: {rows}")


        self.assertEqual(row1_data[0], self.user.username)
        self.assertEqual(row1_data[1], self.user.email)
        self.assertEqual(row1_data[2], self.user.profile.bio)
        self.assertEqual(row1_data[3], self.todo1.title)
        self.assertEqual(row1_data[4], self.todo1.description)
        if hasattr(self, 'project_csv') and self.todo1.project:
             self.assertEqual(row1_data[5], self.todo1.project.name)
        else:
             self.assertEqual(row1_data[5], 'N/A' if not self.todo1.project else self.todo1.project.name)

        self.assertEqual(row1_data[6], self.todo1.get_status_display())
        self.assertEqual(float(row1_data[7]), self.todo1.time_spent_hours)
        self.assertIn(self.todo1.created_at.strftime('%Y-%m-%d'), row1_data[8])
        self.assertIn(self.todo1.updated_at.strftime('%Y-%m-%d'), row1_data[9])


    def test_download_csv_report_no_todos(self):
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
            'Time Spent (hours)', 'Created At', 'Updated At'
        ])
        self.assertEqual(rows[1], [
            self.user.username, self.user.email, self.user.profile.bio,
            'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
        ])

    def test_download_csv_report_without_profile_bio(self):
        self.user.profile.bio = ""
        self.user.profile.save()
        self.client.login(username='csvuser', password='password123')

        TodoItem.objects.filter(user=self.user).exclude(pk=self.todo1.pk).delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        next(reader)
        data_row = next(reader)

        self.assertEqual(data_row[2], "")

    def test_download_csv_report_date_formats(self):
        self.client.login(username='csvuser', password='password123')
        TodoItem.objects.filter(user=self.user, pk=self.todo2.pk).delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        next(reader)
        row = next(reader)

        self.assertEqual(row[8], self.todo1.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(row[9], self.todo1.updated_at.strftime('%Y-%m-%d %H:%M:%S'))

    def test_download_csv_report_user_profile_does_not_exist_gracefully(self):
        self.user.profile.delete()
        self.user.refresh_from_db()

        self.client.login(username='csvuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        reader = csv.reader(StringIO(content))
        next(reader)
        data_row = next(reader)

        self.assertEqual(data_row[0], self.user.username)
        self.assertEqual(data_row[1], self.user.email)
        self.assertEqual(data_row[2], "")

        self.assertTrue(UserProfile.objects.filter(user=self.user).exists(), "Profile should have been recreated by signal.")
        profile = UserProfile.objects.get(user=self.user)
        profile.bio = "Recreated bio for subsequent tests if any"
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

class ProjectMembershipModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='member_user', password='password123')
        self.project = Project.objects.create(name='Membership Test Project')

    def test_unique_user_project_membership(self):
        ProjectMembership.objects.create(project=self.project, user=self.user)
        with self.assertRaises(IntegrityError):
            ProjectMembership.objects.create(project=self.project, user=self.user)

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
        )
        self.assertIsNone(todo.project)

    def test_todo_item_project_set_null_on_delete(self):
        todo = TodoItem.objects.create(user=self.user, title='Task for Project Deletion', project=self.project)
        self.project.delete()
        todo.refresh_from_db()
        self.assertIsNone(todo.project)


class TodoFormWithProjectTests(TodoFormTests):
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(name='Form Test Project', owner=self.user)

    def test_todo_form_valid_with_project(self):
        form_data = {
            'title': 'Form Task with Project',
            'description': 'Form Description',
            'project': self.project.id,
            'status': 'todo'
        }
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        todo = form.save(commit=False)
        self.assertEqual(todo.project, self.project)

    def test_todo_form_valid_without_project(self):
        super().test_todo_form_valid_without_time_spent()
        form_data = {'title': 'Form Task No Project', 'description': 'Desc', 'status': 'todo'}
        form = TodoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        todo = form.save(commit=False)
        self.assertIsNone(todo.project)


class TodoViewWithProjectTests(TodoViewTests):
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(name='View Test Project', owner=self.user)
        ProjectMembership.objects.create(project=self.project, user=self.user)

    def test_add_todo_view_with_project(self):
        url = reverse('add_todo')
        post_data = {
            'title': 'View Add Task with Project',
            'description': 'View Add Description',
            'project': self.project.id,
            'status': 'inprogress'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        created_task = TodoItem.objects.get(user=self.user, title='View Add Task with Project')
        self.assertEqual(created_task.project, self.project)

    def test_add_todo_view_without_project(self):
        url = reverse('add_todo')
        post_data = {
            'title': 'View Add Task No Project',
            'description': 'View Add Description',
            'status': 'todo'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        created_task = TodoItem.objects.get(user=self.user, title='View Add Task No Project')
        self.assertIsNone(created_task.project)

    def test_edit_todo_view_loads_and_saves_project(self):
        task = TodoItem.objects.create(user=self.user, title='Task for Project Edit', description="Initial Description", project=self.project)
        project2 = Project.objects.create(name='Project Two', owner=self.user)

        url = reverse('edit_todo', args=[task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['project'], self.project.id)

        post_data_change = {
            'title': task.title,
            'description': task.description,
            'project': project2.id,
            'status': task.status
        }
        response = self.client.post(url, post_data_change)
        self.assertEqual(response.status_code, 302, response.content.decode() if response.status_code !=302 else None)
        task.refresh_from_db()
        self.assertEqual(task.project, project2)

        post_data_remove = {
            'title': task.title,
            'description': task.description,
            'project': '',
            'status': task.status
        }
        response = self.client.post(url, post_data_remove)
        self.assertEqual(response.status_code, 302, response.content.decode() if response.status_code !=302 else None)
        task.refresh_from_db()
        self.assertIsNone(task.project)

    def test_inline_edit_todo_updates_project(self):
        task = TodoItem.objects.create(user=self.user, title='Inline Edit Project Task', project=None)
        project2 = Project.objects.create(name='Project For Inline Edit', owner=self.user)
        url = reverse('inline_edit_todo', args=[task.id])

        edit_data = {'project_id': project2.id}
        response = self.client.post(url, json.dumps(edit_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertEqual(json_response['todo']['project_id'], project2.id)
        self.assertEqual(json_response['todo']['project_name'], project2.name)
        task.refresh_from_db()
        self.assertEqual(task.project, project2)

        edit_data = {'project_id': None}
        response = self.client.post(url, json.dumps(edit_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertIsNone(json_response['todo']['project_id'])
        task.refresh_from_db()
        self.assertIsNone(task.project)

    def test_api_get_kanban_tasks_includes_project(self):
        TodoItem.objects.create(user=self.user, title='Kanban Task With Project', project=self.project)
        TodoItem.objects.create(user=self.user, title='Kanban Task No Project')
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

class CSVReportWithProjectTests(CSVReportTests):
    def setUp(self):
        super().setUp()
        self.project_csv = Project.objects.create(name='CSV Test Project', owner=self.user)
        self.todo1.project = self.project_csv
        self.todo1.save()

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
        self.assertEqual(len(rows), 2)

        row_todo1 = next(r for r in rows if r[3] == self.todo1.title)
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

        self.project_owner_only = Project.objects.create(name='Project Delta (Owner Access Test)', owner=self.user1, description='Owned by user1')

        self.project_list_url = reverse('project_list')

    def test_project_list_view_login_required(self):
        response = self.client.get(self.project_list_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_project_list_view_displays_member_projects(self):
        self.client.login(username='user1_proj_view', password='password123')
        response = self.client.get(self.project_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project1.name)
        self.assertContains(response, self.project2.name)
        self.assertNotContains(response, self.project3.name)
        self.assertEqual(len(response.context['projects']), 2)

    def test_project_list_view_empty_for_non_member(self):
        user3 = User.objects.create_user(username='user3_no_projects', password='password123')
        self.client.login(username='user3_no_projects', password='password123')
        response = self.client.get(self.project_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You are not currently a member of any projects.")
        self.assertEqual(len(response.context['projects']), 0)

    def test_project_detail_view_login_required(self):
        project_detail_url = reverse('project_detail', args=[self.project1.pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_project_detail_view_member_access(self):
        self.client.login(username='user1_proj_view', password='password123')
        project_detail_url = reverse('project_detail', args=[self.project1.pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project1.name)
        self.assertContains(response, self.project1.description)
        self.assertContains(response, self.user1.username)

    def test_project_detail_view_owner_access_without_membership(self):
        self.client.login(username='user1_proj_view', password='password123')
        self.assertNotIn(self.user1, self.project_owner_only.members.all())
        self.assertEqual(self.project_owner_only.owner, self.user1)

        project_detail_url = reverse('project_detail', args=[self.project_owner_only.pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project_owner_only.name)
        self.assertContains(response, self.user1.username)

    def test_project_detail_view_non_owner_non_member_access_denied(self):
        self.client.login(username='user1_proj_view', password='password123')
        project_detail_url_gamma = reverse('project_detail', args=[self.project3.pk])
        response = self.client.get(project_detail_url_gamma)
        self.assertEqual(response.status_code, 403)

    def test_project_detail_view_displays_members(self):
        self.client.login(username='user1_proj_view', password='password123')
        project_detail_url = reverse('project_detail', args=[self.project2.pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project2.name)
        self.assertContains(response, self.user1.username)
        self.assertContains(response, self.user1.email)
        self.assertContains(response, self.user2.username)
        self.assertContains(response, self.user2.email)
        self.assertEqual(response.context['project'].members.count(), 2)
        members_in_context = [member.username for member in response.context['members']]
        self.assertIn(self.user1.username, members_in_context)
        self.assertIn(self.user2.username, members_in_context)

    def test_project_detail_view_non_existent_project(self):
        self.client.login(username='user1_proj_view', password='password123')
        non_existent_pk = 9999
        project_detail_url = reverse('project_detail', args=[non_existent_pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 404)

    def test_project_detail_view_displays_associated_tasks(self):
        self.client.login(username='user1_proj_view', password='password123')

        task1_p1 = TodoItem.objects.create(user=self.user1, title="Task 1 for Project Alpha", project=self.project1, description="Desc P1T1")
        task2_p1 = TodoItem.objects.create(user=self.user1, title="Task 2 for Project Alpha", project=self.project1, description="Desc P1T2", status="inprogress")

        task1_p2 = TodoItem.objects.create(user=self.user1, title="Task 1 for Project Beta", project=self.project2, description="Desc P2T1")

        project_detail_url = reverse('project_detail', args=[self.project1.pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, task1_p1.title)
        self.assertContains(response, task1_p1.get_status_display())
        self.assertContains(response, task2_p1.title)
        self.assertContains(response, task2_p1.get_status_display())
        self.assertNotContains(response, task1_p2.title)

        self.assertIn('tasks', response.context)
        context_tasks = response.context['tasks']
        self.assertEqual(len(context_tasks), 2)
        self.assertIn(task1_p1, context_tasks)
        self.assertIn(task2_p1, context_tasks)

        self.assertContains(response, f'href="{reverse("todo_detail", args=[task1_p1.pk])}"')


    def test_project_detail_view_no_tasks(self):
        self.client.login(username='user1_proj_view', password='password123')
        project_detail_url = reverse('project_detail', args=[self.project_owner_only.pk])
        response = self.client.get(project_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No tasks currently associated with this project.")
        self.assertIn('tasks', response.context)
        self.assertEqual(len(response.context['tasks']), 0)

class TodoLogViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testloguser', password='password123')
        self.client.login(username='testloguser', password='password123')
        self.task = TodoItem.objects.create(user=self.user, title='Task for Log', description='Log Description')

    def test_add_log_to_todo(self):
        """Test that a log can be added to a todo item."""
        url = reverse('add_log_to_todo', args=[self.task.id])
        post_data = {
            'log_time': 1.5,
            'task_date': '2025-01-01',
            'notes': 'Test log notes'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('todo_detail', args=[self.task.id]))
        self.assertEqual(self.task.logs.count(), 1)
        log = self.task.logs.first()
        self.assertEqual(log.log_time, 1.5)
        self.assertEqual(log.task_date.strftime('%Y-%m-%d'), '2025-01-01')
        self.assertEqual(log.notes, 'Test log notes')

    def test_add_log_to_todo(self):
        """Test that a log can be added to a todo item."""
        task = TodoItem.objects.create(user=self.user, title='Task for Log', description='Log Description')
        url = reverse('add_log_to_todo', args=[task.id])
        post_data = {
            'log_time': 1.5,
            'task_date': '2025-01-01',
            'notes': 'Test log notes'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('todo_detail', args=[task.id]))
        self.assertEqual(task.logs.count(), 1)
        log = task.logs.first()
        self.assertEqual(log.log_time, 1.5)
        self.assertEqual(log.task_date.strftime('%Y-%m-%d'), '2025-01-01')
        self.assertEqual(log.notes, 'Test log notes')

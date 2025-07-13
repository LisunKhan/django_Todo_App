from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Project, TodoItem

class Command(BaseCommand):
    help = 'Sets up initial data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Setting up test data...')

        # Create superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'password')
            self.stdout.write(self.style.SUCCESS('Successfully created superuser "admin"'))

        # Create regular user
        if not User.objects.filter(username='testuser').exists():
            user = User.objects.create_user('testuser', 'testuser@example.com', 'password')
            self.stdout.write(self.style.SUCCESS('Successfully created user "testuser"'))
        else:
            user = User.objects.get(username='testuser')

        # Create project
        if not Project.objects.filter(name='Test Project').exists():
            project = Project.objects.create(name='Test Project', owner=User.objects.get(username='admin'))
            project.members.add(user)
            self.stdout.write(self.style.SUCCESS('Successfully created project "Test Project"'))
        else:
            project = Project.objects.get(name='Test Project')

        # Create tasks
        if not TodoItem.objects.filter(title='Task 1').exists():
            TodoItem.objects.create(title='Task 1', project=project, user=user)
            self.stdout.write(self.style.SUCCESS('Successfully created task "Task 1"'))

        if not TodoItem.objects.filter(title='Task 2').exists():
            TodoItem.objects.create(title='Task 2', project=project, user=user)
            self.stdout.write(self.style.SUCCESS('Successfully created task "Task 2"'))

        self.stdout.write(self.style.SUCCESS('Test data setup complete.'))

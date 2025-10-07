from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from restaurant.models import UserProfile

class Command(BaseCommand):
    help = 'Create users for each role with password admin123'

    def handle(self, *args, **options):
        usernames_roles = {
            'mesero': 'garzon',
            'cocinero': 'cocinero',
            'admin': 'admin',
            'recepcion': 'recepcion'
        }
        for username, role in usernames_roles.items():
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, password='admin123')
                user_profile = user.userprofile  # Signal creates it
                user_profile.role = role
                user_profile.save()
                self.stdout.write(self.style.SUCCESS(f'Created user {username} with role {role}'))
            else:
                self.stdout.write(f'User {username} already exists')

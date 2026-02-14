from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username='pavan').exists():
            User.objects.create_superuser(
                username='pavan',
                email='pavanmamidi1432@gmail.com',
                password='pandu'
            )
            self.stdout.write(self.style.SUCCESS('Superuser created'))
        else:
            self.stdout.write('Superuser already exists')

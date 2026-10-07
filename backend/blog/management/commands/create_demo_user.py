import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the demo login (DEMO_USER / DEMO_PASSWORD) if it does not exist."

    def handle(self, *args, **opts):
        name = os.environ.get("DEMO_USER", "demo")
        pwd = os.environ.get("DEMO_PASSWORD", "demo12345")
        User = get_user_model()
        user, created = User.objects.get_or_create(username=name)
        if created:
            user.set_password(pwd)
            user.save()
        self.stdout.write(f"demo user '{name}' {'created' if created else 'exists'}")

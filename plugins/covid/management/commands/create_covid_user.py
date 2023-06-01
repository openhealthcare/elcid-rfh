"""
Management Command to create a covid user
"""
import random

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from opal.models import UserProfile, Role


def pw_please():
    numbers = ['123', '456', '789']
    nouns = ['Drums', 'Apples', 'Rabbits']
    symbols = ['?', '!', ';']

    return random.choice(numbers) + random.choice(nouns) + random.choice(symbols)

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('email')

    def handle(self, *args, **kwargs):

        email = kwargs['email']
        existing_user = User.objects.filter(email=email).first()
        if existing_user is not None:
            raise ValueError(
                f"Email is currently in use by {existing_user.username}"
            )
        username, _ = email.split('@')

        user = User(username=username)

        password = pw_please()

        user.set_password(password)

        user.first_name = username
        user.email = email
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.force_password_change = True
        profile.save()

        for role_name in ['view_lab_tests_in_list', 'view_lab_tests_in_detail', 'view_lab_test_trends', 'covid19']:
            profile.roles.add(Role.objects.get(name=role_name))


        title = 'Your new elCID account'
        plain_message = """An account has been created for you on the Elcid database at the Royal Free.

You can access the system at the hospital or via VPN at http://elcid-rfh/

Your username is {username}

Your password has been set to {password}

You will be asked to change it the first time you log in.

Feel free to contact support@openhealthcare.org.uk if you encounter any issues.""".format(
    username=username,
    password=password)

        send_mail(
            title,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )

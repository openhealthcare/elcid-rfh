# Generated by Django 2.0.13 on 2021-05-06 10:21

from django.db import migrations

from plugins.ipc.constants import IPC_ROLE

def add(apps, schema_editor):
    Role = apps.get_model("opal", "Role")
    UserProfile = apps.get_model("opal", "UserProfile")

    role, _ = Role.objects.get_or_create(
        name=IPC_ROLE
    )

    user_profiles = UserProfile.objects.filter(user__is_superuser=True)

    for user_profile in user_profiles:
        existing_roles = set(user_profile.roles.values_list(
            'name', flat=True
        ))
        if not IPC_ROLE in existing_roles:
            user_profile.roles.add(role)


def remove(apps, schema_editor):
    Role = apps.get_model("opal", "Role")
    Role.objects.filter(name=IPC_ROLE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ipc', '0002_auto_20210421_1102'),
    ]

    operations = [
        migrations.RunPython(
            add, reverse_code=remove
        )
    ]
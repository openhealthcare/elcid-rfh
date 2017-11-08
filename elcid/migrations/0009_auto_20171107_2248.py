# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from intrahospital_api import constants


def add(apps, schema_editor):
    Role = apps.get_model("opal", "Role")
    UserProfile = apps.get_model("opal", "UserProfile")

    for role_name in constants.INTRAHOSPITAL_ROLES:
        Role.objects.get_or_create(
            name=role_name
        )

    user_profiles = UserProfile.objects.filter(user__is_superuser=True)

    for user_profile in user_profiles:
        existing_roles = set(user_profile.roles.values_list(
            'name', flat=True
        ))
        role_names_to_add = constants.INTRAHOSPITAL_ROLES - existing_roles
        roles_to_add = Role.objects.filter(name__in=role_names_to_add)
        user_profile.roles.add(*roles_to_add)


def remove(apps, schema_editor):
    Role = apps.get_model("opal", "Role")
    Role.objects.filter(role__name__in=constants.INTRAHOSPITAL_ROLES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0008_auto_20170720_1210'),
    ]

    operations = [
        migrations.RunPython(
            add, reverse_code=remove
        )
    ]

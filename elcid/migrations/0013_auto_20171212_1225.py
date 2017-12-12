# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0012_auto_20171212_1207'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='presentingcomplaint',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='presentingcomplaint',
            name='episode',
        ),
        migrations.RemoveField(
            model_name='presentingcomplaint',
            name='symptom_fk',
        ),
        migrations.RemoveField(
            model_name='presentingcomplaint',
            name='symptoms',
        ),
        migrations.RemoveField(
            model_name='presentingcomplaint',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='PresentingComplaint',
        ),
    ]

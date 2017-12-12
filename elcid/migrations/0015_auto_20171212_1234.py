# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0014_auto_20171212_1231'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='secondarydiagnosis',
            name='condition_fk',
        ),
        migrations.RemoveField(
            model_name='secondarydiagnosis',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='secondarydiagnosis',
            name='episode',
        ),
        migrations.RemoveField(
            model_name='secondarydiagnosis',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='SecondaryDiagnosis',
        ),
    ]

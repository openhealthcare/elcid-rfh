# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0011_auto_20171212_1122'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='carers',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='carers',
            name='patient',
        ),
        migrations.RemoveField(
            model_name='carers',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='Carers',
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0004_auto_20170208_2102'),
    ]

    operations = [
        migrations.AlterField(
            model_name='positivebloodculturehistory',
            name='when',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]

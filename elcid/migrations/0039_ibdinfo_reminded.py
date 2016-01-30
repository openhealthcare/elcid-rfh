# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0038_ibdinfo_last_blood'),
    ]

    operations = [
        migrations.AddField(
            model_name='ibdinfo',
            name='reminded',
            field=models.BooleanField(default=False),
        ),
    ]

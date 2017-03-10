# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0002_auto_20170122_1715'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='bed',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]

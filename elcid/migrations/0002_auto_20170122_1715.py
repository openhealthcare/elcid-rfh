# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contactdetails',
            name='city',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
    ]

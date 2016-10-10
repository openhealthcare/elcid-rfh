# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0008_auto_20161006_1059'),
    ]

    operations = [
        migrations.AddField(
            model_name='microbiologyinput',
            name='infection_control',
            field=models.TextField(blank=True),
        ),
    ]

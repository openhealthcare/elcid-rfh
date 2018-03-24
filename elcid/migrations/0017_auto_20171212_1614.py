# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0016_auto_20171212_1252'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='diagnosis',
            options={},
        ),
        migrations.AlterField(
            model_name='diagnosis',
            name='provisional',
            field=models.BooleanField(default=False, help_text=b'True if the diagnosis is provisional. Defaults to False', verbose_name=b'Provisional?'),
        ),
    ]

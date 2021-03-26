# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-06-15 10:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0017_auto_20180108_1614'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='diagnosis',
            options={'verbose_name': 'Diagnosis / Issues', 'verbose_name_plural': 'Diagnoses'},
        ),
        migrations.AlterField(
            model_name='diagnosis',
            name='provisional',
            field=models.BooleanField(default=False, help_text=b'True if the diagnosis is provisional. Defaults to False', verbose_name=b'Provisional?'),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-10-18 13:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tb', '0034_auto_20180824_1925'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tbmanagement',
            options={'verbose_name': 'TB Management'},
        ),
        migrations.AlterField(
            model_name='tbmanagement',
            name='ltbr_number',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name=b'LTBR Number'),
        ),
    ]

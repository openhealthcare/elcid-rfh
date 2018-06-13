# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-06-13 16:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tb', '0026_auto_20180613_1600'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accessconsiderations',
            name='finance',
        ),
        migrations.RemoveField(
            model_name='accessconsiderations',
            name='provision',
        ),
        migrations.AddField(
            model_name='accessconsiderations',
            name='access_assistance',
            field=models.CharField(blank=True, choices=[(b'provision', b'provision'), (b'finance', b'finance')], max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='homelessness',
            field=models.CharField(blank=True, choices=[(b'Never', b'Never'), (b'Current', b'Current'), (b'Past', b'Past')], max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='homelessness_type',
            field=models.CharField(blank=True, choices=[(b'Hostel', b'Hostel'), (b'Sofa surfing', b'Sofa surfing'), (b'Street', b'Street'), (b'Other', b'Other')], max_length=256, null=True),
        ),
    ]

# Generated by Django 2.2.16 on 2023-01-09 15:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0067_auto_20221209_1453'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mergedmrn',
            name='upstream_merge_datetime',
        ),
    ]

# Generated by Django 2.0.13 on 2021-12-14 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipc', '0005_ipcstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='ipcstatus',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
    ]

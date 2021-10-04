# Generated by Django 2.0.13 on 2021-09-30 11:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0040_auto_20201007_1346'),
        ('ipc', '0005_ipcstatus'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ipcstatus',
            name='episode',
        ),
        migrations.AddField(
            model_name='ipcstatus',
            name='patient',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
            preserve_default=False,
        ),
    ]
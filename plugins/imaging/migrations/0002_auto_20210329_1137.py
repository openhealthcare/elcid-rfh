# Generated by Django 2.0.13 on 2021-03-29 11:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('imaging', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patientimagingstatus',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='patientimagingstatus',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='patientimagingstatus',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_imaging_patientimagingstatus_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='patientimagingstatus',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='patientimagingstatus',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='patientimagingstatus',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_imaging_patientimagingstatus_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
    ]

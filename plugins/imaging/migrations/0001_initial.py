# Generated by Django 2.0.13 on 2020-06-04 19:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import opal.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('opal', '0037_auto_20181114_1445'),
    ]

    operations = [
        migrations.CreateModel(
            name='Imaging',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sql_id', models.IntegerField(blank=True, null=True)),
                ('patient_number', models.CharField(blank=True, max_length=255, null=True)),
                ('patient_surname', models.CharField(blank=True, max_length=255, null=True)),
                ('patient_forename', models.CharField(blank=True, max_length=255, null=True)),
                ('result_id', models.CharField(blank=True, max_length=255, null=True)),
                ('order_number', models.CharField(blank=True, max_length=255, null=True)),
                ('order_effective_date', models.DateTimeField(blank=True, null=True)),
                ('date_of_result', models.DateTimeField(blank=True, null=True)),
                ('date_reported', models.DateTimeField(blank=True, null=True)),
                ('requesting_user_code', models.CharField(blank=True, max_length=255, null=True)),
                ('requesting_user_name', models.CharField(blank=True, max_length=255, null=True)),
                ('cerner_visit_id', models.CharField(blank=True, max_length=255, null=True)),
                ('result_code', models.CharField(blank=True, max_length=255, null=True)),
                ('result_description', models.CharField(blank=True, max_length=255, null=True)),
                ('result_status', models.CharField(blank=True, max_length=255, null=True)),
                ('obx_result', models.TextField(blank=True, null=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imaging', to='opal.Patient')),
            ],
        ),
        migrations.CreateModel(
            name='PatientImagingStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('updated', models.DateTimeField(blank=True, null=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('has_imaging', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_imaging_patientimagingstatus_subrecords', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_imaging_patientimagingstatus_subrecords', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
    ]

# Generated by Django 2.0.13 on 2021-08-17 16:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0040_auto_20201007_1346'),
        ('labtests', '0007_add_reported_datetime'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservationHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('observation_datetime', models.DateTimeField(blank=True, null=True)),
                ('reported_datetime', models.DateTimeField(blank=True, null=True)),
                ('observation_name', models.CharField(blank=True, max_length=256, null=True)),
                ('observation_number', models.CharField(blank=True, max_length=256, null=True)),
                ('observation_value', models.TextField(blank=True, null=True)),
                ('reference_range', models.CharField(blank=True, max_length=256, null=True)),
                ('units', models.CharField(blank=True, max_length=256, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('test_name', models.CharField(blank=True, max_length=256, null=True)),
                ('lab_number', models.CharField(blank=True, max_length=256, null=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='observation_history', to='opal.Patient')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import opal.models


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0032_auto_20171020_1058'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalDemographics',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('updated', models.DateTimeField(null=True, blank=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('hospital_number', models.CharField(max_length=255, blank=True)),
                ('nhs_number', models.CharField(max_length=255, null=True, blank=True)),
                ('surname', models.CharField(max_length=255, blank=True)),
                ('first_name', models.CharField(max_length=255, blank=True)),
                ('middle_name', models.CharField(max_length=255, null=True, blank=True)),
                ('date_of_birth', models.DateField(null=True, blank=True)),
                ('reconciled', models.BooleanField(default=False)),
                ('title_ft', models.CharField(default=b'', max_length=255, null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='created_intrahospital_api_externaldemographics_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)),
                ('patient', models.ForeignKey(to='opal.Patient', on_delete=models.CASCADE)),
                ('title_fk', models.ForeignKey(blank=True, to='opal.Title', null=True, on_delete=models.CASCADE)),
                ('updated_by', models.ForeignKey(related_name='updated_intrahospital_api_externaldemographics_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
    ]

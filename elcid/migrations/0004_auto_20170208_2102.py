# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import opal.models


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0028_auto_20170208_2102'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('elcid', '0003_auto_20170122_1723'),
    ]

    operations = [
        migrations.CreateModel(
            name='PositiveBloodCultureHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('updated', models.DateTimeField(null=True, blank=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('when', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(related_name='created_elcid_positivebloodculturehistory_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('patient', models.ForeignKey(to='opal.Patient')),
                ('updated_by', models.ForeignKey(related_name='updated_elcid_positivebloodculturehistory_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
        migrations.RemoveField(
            model_name='result',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='result',
            name='patient',
        ),
        migrations.RemoveField(
            model_name='result',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='Result',
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import opal.models


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0009_glossolaliasubscription'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('elcid', '0035_finaldiagnosis'),
    ]

    operations = [
        migrations.CreateModel(
            name='Imaging',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('updated', models.DateTimeField(null=True, blank=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('date', models.DateField(null=True, blank=True)),
                ('site', models.CharField(max_length=200, null=True, blank=True)),
                ('details', models.TextField(null=True, blank=True)),
                ('imaging_type_ft', models.CharField(default=b'', max_length=255, null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='created_elcid_imaging_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('episode', models.ForeignKey(to='opal.Episode')),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ImagingTypes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='imaging',
            name='imaging_type_fk',
            field=models.ForeignKey(blank=True, to='elcid.ImagingTypes', null=True),
        ),
        migrations.AddField(
            model_name='imaging',
            name='updated_by',
            field=models.ForeignKey(related_name='updated_elcid_imaging_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]

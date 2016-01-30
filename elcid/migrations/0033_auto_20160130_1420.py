# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import opal.models


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0008_auto_20151216_1803'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('elcid', '0032_auto_20151207_0856'),
    ]

    operations = [
        migrations.CreateModel(
            name='IBDInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('updated', models.DateTimeField(null=True, blank=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('next_blood', models.DateField(null=True, blank=True)),
                ('consultant_ft', models.CharField(default=b'', max_length=255, null=True, blank=True)),
                ('schedule_ft', models.CharField(default=b'', max_length=255, null=True, blank=True)),
                ('consultant_fk', models.ForeignKey(blank=True, to='elcid.Consultant', null=True)),
                ('created_by', models.ForeignKey(related_name='created_elcid_ibdinfo_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('episode', models.ForeignKey(to='opal.Episode')),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Schedules',
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
            model_name='ibdinfo',
            name='schedule_fk',
            field=models.ForeignKey(blank=True, to='elcid.Schedules', null=True),
        ),
        migrations.AddField(
            model_name='ibdinfo',
            name='updated_by',
            field=models.ForeignKey(related_name='updated_elcid_ibdinfo_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]

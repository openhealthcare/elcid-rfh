# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import opal.models


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0008_auto_20151216_1803'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('elcid', '0033_auto_20160130_1420'),
    ]

    operations = [
        migrations.CreateModel(
            name='Platelets',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('updated', models.DateTimeField(null=True, blank=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('result', models.CharField(max_length=200)),
                ('reviewed', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(related_name='created_elcid_platelets_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('episode', models.ForeignKey(to='opal.Episode')),
                ('updated_by', models.ForeignKey(related_name='updated_elcid_platelets_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, models.Model),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import opal.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('opal', '0010_auto_20160212_1404'),
        ('elcid', '0034_auto_20160212_1405'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinalDiagnosis',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('updated', models.DateTimeField(null=True, blank=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('source', models.CharField(max_length=255, blank=True)),
                ('contaminant', models.BooleanField(default=False)),
                ('community_related', models.BooleanField(default=False)),
                ('hcai_related', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(related_name='created_elcid_finaldiagnosis_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('episode', models.ForeignKey(to='opal.Episode')),
                ('updated_by', models.ForeignKey(related_name='updated_elcid_finaldiagnosis_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, models.Model),
        ),
    ]

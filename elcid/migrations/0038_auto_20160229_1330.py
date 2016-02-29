# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0037_auto_20160229_1247'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='opatreview',
            name='fistula',
        ),
        migrations.RemoveField(
            model_name='opatreview',
            name='graft',
        ),
        migrations.RemoveField(
            model_name='opatreview',
            name='tunnelled_or_temp',
        ),
        migrations.AddField(
            model_name='line',
            name='fistula',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='line',
            name='graft',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='line',
            name='tunnelled_or_temp',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]

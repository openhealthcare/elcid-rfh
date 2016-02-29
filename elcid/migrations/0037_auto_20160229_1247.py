# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0036_auto_20160222_1823'),
    ]

    operations = [
        migrations.AddField(
            model_name='opatreview',
            name='fistula',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='opatreview',
            name='graft',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='opatreview',
            name='tunnelled_or_temp',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]

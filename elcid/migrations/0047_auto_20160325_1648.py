# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0012_maritalstatus_title'),
        ('elcid', '0046_result'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='demographics',
            name='name',
        ),
        migrations.AddField(
            model_name='demographics',
            name='ethnicity_fk',
            field=models.ForeignKey(blank=True, to='opal.Ethnicity', null=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='ethnicity_ft',
            field=models.CharField(default=b'', max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='marital_status_fk',
            field=models.ForeignKey(blank=True, to='opal.MaritalStatus', null=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='marital_status_ft',
            field=models.CharField(default=b'', max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='religion',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]

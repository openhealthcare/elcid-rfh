# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0032_auto_20171020_1058'),
        ('intrahospital_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='externaldemographics',
            name='sex_fk',
            field=models.ForeignKey(blank=True, to='opal.Gender', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='externaldemographics',
            name='sex_ft',
            field=models.CharField(default=b'', max_length=255, null=True, blank=True),
        ),
    ]

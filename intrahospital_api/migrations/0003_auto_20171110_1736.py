# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0032_auto_20171020_1058'),
        ('intrahospital_api', '0002_auto_20171109_2039'),
    ]

    operations = [
        migrations.AddField(
            model_name='externaldemographics',
            name='ethnicity_fk',
            field=models.ForeignKey(blank=True, to='opal.Ethnicity', null=True),
        ),
        migrations.AddField(
            model_name='externaldemographics',
            name='ethnicity_ft',
            field=models.CharField(default=b'', max_length=255, null=True, blank=True),
        ),
    ]

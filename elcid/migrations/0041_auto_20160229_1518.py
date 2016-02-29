# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0040_auto_20160229_1517'),
    ]

    operations = [
        migrations.AddField(
            model_name='primarydiagnosis',
            name='condition_fk',
            field=models.ForeignKey(blank=True, to='elcid.PrimaryDiagnosisCondition', null=True),
        ),
        migrations.AddField(
            model_name='primarydiagnosis',
            name='condition_ft',
            field=models.CharField(default=b'', max_length=255, null=True, blank=True),
        ),
    ]

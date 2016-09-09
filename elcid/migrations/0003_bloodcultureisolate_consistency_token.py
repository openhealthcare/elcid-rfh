# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0002_auto_20160620_1452'),
    ]

    operations = [
        migrations.AddField(
            model_name='bloodcultureisolate',
            name='consistency_token',
            field=models.CharField(default=1, max_length=8),
            preserve_default=False,
        ),
    ]

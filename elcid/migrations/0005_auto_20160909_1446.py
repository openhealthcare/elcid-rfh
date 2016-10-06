# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0004_auto_20160909_1106'),
    ]

    operations = [
        migrations.AddField(
            model_name='labtest',
            name='consistency_token',
            field=models.CharField(default=1, max_length=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='labtest',
            name='test_name',
            field=models.CharField(default='fish', max_length=256),
            preserve_default=False,
        ),
    ]

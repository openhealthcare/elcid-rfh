# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intrahospital_api', '0003_auto_20171110_1736'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='externaldemographics',
            name='reconciled',
        ),
    ]

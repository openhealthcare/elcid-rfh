# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0006_auto_20170220_1108'),
    ]

    operations = [
        migrations.RenameField(
            model_name='microbiologytest',
            old_name='datetime_ordered',
            new_name='date_ordered',
        ),
    ]

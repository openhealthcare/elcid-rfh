# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0037_auto_20160130_1443'),
    ]

    operations = [
        migrations.AddField(
            model_name='ibdinfo',
            name='last_blood',
            field=models.DateField(null=True, blank=True),
        ),
    ]

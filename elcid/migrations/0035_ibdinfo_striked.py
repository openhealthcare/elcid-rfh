# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0034_platelets'),
    ]

    operations = [
        migrations.AddField(
            model_name='ibdinfo',
            name='striked',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0035_ibdinfo_striked'),
    ]

    operations = [
        migrations.AddField(
            model_name='demographics',
            name='weight',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]

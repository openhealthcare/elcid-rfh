# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0044_auto_20160324_1644'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='demographics',
            name='ethnicity_old',
        ),
        migrations.RemoveField(
            model_name='demographics',
            name='gender',
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0039_auto_20160229_1413'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='primarydiagnosis',
            name='condition_fk',
        ),
        migrations.RemoveField(
            model_name='primarydiagnosis',
            name='condition_ft',
        ),
    ]

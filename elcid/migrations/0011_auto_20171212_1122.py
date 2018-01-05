# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0010_auto_20171211_1321'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contactdetails',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='contactdetails',
            name='patient',
        ),
        migrations.RemoveField(
            model_name='contactdetails',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='ContactDetails',
        ),
    ]

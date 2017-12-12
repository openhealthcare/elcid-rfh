# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0013_auto_20171212_1225'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='consultantatdischarge',
            name='consultant_fk',
        ),
        migrations.RemoveField(
            model_name='consultantatdischarge',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='consultantatdischarge',
            name='episode',
        ),
        migrations.RemoveField(
            model_name='consultantatdischarge',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='ConsultantAtDischarge',
        ),
    ]

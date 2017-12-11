# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0032_auto_20171020_1058'),
        ('elcid', '0010_auto_20171211_1321'),
    ]

    operations = [
        migrations.AddField(
            model_name='allergies',
            name='drug_temp_fk',
            field=models.ForeignKey(blank=True, to='opal.Drug', null=True),
        ),
        migrations.AddField(
            model_name='allergies',
            name='drug_temp_ft',
            field=models.CharField(default=b'', max_length=255, null=True, blank=True),
        ),
    ]

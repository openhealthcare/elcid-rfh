# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import elcid.models


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '0006_auto_20171024_1543'),
        ('elcid', '0006_auto_20170220_1108'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organism',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('lab.observation', elcid.models.RfhObservation),
        ),
    ]

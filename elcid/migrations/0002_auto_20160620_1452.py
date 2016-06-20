# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bloodcultureisolate',
            name='organism',
            field=models.ForeignKey(related_name='blood_culture_isolate_organisms', blank=True, to='opal.Microbiology_organism', null=True),
        ),
    ]

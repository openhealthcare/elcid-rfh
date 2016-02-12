# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0033_auto_20160212_1404'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='episodeofneutropenia',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='episodeofneutropenia',
            name='patient',
        ),
        migrations.RemoveField(
            model_name='episodeofneutropenia',
            name='updated_by',
        ),
        migrations.RemoveField(
            model_name='haeminformation',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='haeminformation',
            name='patient',
        ),
        migrations.RemoveField(
            model_name='haeminformation',
            name='patient_type_fk',
        ),
        migrations.RemoveField(
            model_name='haeminformation',
            name='type_of_chemotherapy_fk',
        ),
        migrations.RemoveField(
            model_name='haeminformation',
            name='type_of_transplant_fk',
        ),
        migrations.RemoveField(
            model_name='haeminformation',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='EpisodeOfNeutropenia',
        ),
        migrations.DeleteModel(
            name='HaemChemotherapyType',
        ),
        migrations.DeleteModel(
            name='HaemInformation',
        ),
        migrations.DeleteModel(
            name='HaemInformationType',
        ),
        migrations.DeleteModel(
            name='HaemTransplantType',
        ),
    ]

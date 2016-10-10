# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '__first__'),
        ('elcid', '0005_auto_20160909_1446'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fish',
            name='labtest_ptr',
        ),
        migrations.RemoveField(
            model_name='labtest',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='labtest',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='labtest',
            name='resistant_antibiotics',
        ),
        migrations.RemoveField(
            model_name='labtest',
            name='sensitive_antibiotics',
        ),
        migrations.RemoveField(
            model_name='labtest',
            name='updated_by',
        ),
        migrations.CreateModel(
            name='GNR',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('lab.labtest',),
        ),
        migrations.CreateModel(
            name='GPCStaph',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('lab.labtest',),
        ),
        migrations.CreateModel(
            name='GPCStrep',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('lab.labtest',),
        ),
        migrations.CreateModel(
            name='GramStain',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('lab.labtest',),
        ),
        migrations.CreateModel(
            name='Organism',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('lab.labtest',),
        ),
        migrations.CreateModel(
            name='QuickFISH',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('lab.labtest',),
        ),
        migrations.RemoveField(
            model_name='bloodcultureisolate',
            name='microscopy',
        ),
        migrations.RemoveField(
            model_name='bloodcultureisolate',
            name='organism',
        ),
        migrations.RemoveField(
            model_name='bloodcultureisolate',
            name='resistant_antibiotics',
        ),
        migrations.RemoveField(
            model_name='bloodcultureisolate',
            name='sensitive_antibiotics',
        ),
        migrations.DeleteModel(
            name='Fish',
        ),
        migrations.DeleteModel(
            name='LabTest',
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-13 10:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0025_merge_20180718_0817'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='finaldiagnosis',
            options={'verbose_name': 'Final Diagnosis', 'verbose_name_plural': 'Final Diagnoses'},
        ),
        migrations.AlterModelOptions(
            name='infection',
            options={'verbose_name': 'Infection Related Issues'},
        ),
        migrations.AlterModelOptions(
            name='microbiologyinput',
            options={'verbose_name': 'Clinical Advice', 'verbose_name_plural': 'Clinical Advice'},
        ),
        migrations.AlterModelOptions(
            name='pastmedicalhistory',
            options={'verbose_name': 'PMH', 'verbose_name_plural': 'Past medical histories'},
        ),
        migrations.AlterModelOptions(
            name='primarydiagnosis',
            options={'verbose_name': 'Primary Diagnosis', 'verbose_name_plural': 'Primary Diagnoses'},
        ),
        migrations.AlterModelOptions(
            name='procedure',
            options={'verbose_name': 'Operation / Procedures'},
        ),
        migrations.AlterModelOptions(
            name='referralroute',
            options={'verbose_name': 'Referral Route'},
        ),
        migrations.AlterModelOptions(
            name='symptomcomplex',
            options={'verbose_name': 'Symptoms', 'verbose_name_plural': 'Symptom complexes'},
        ),
        migrations.AlterField(
            model_name='referralroute',
            name='referral_type',
            field=models.CharField(blank=True, choices=[(b'Primary care (GP)', b'Primary care (GP)'), (b'Primary care (other)', b'Primary care (other)'), (b'Secondary care', b'Secondary care'), (b'TB service', b'TB service'), (b'A&E', b'A&E'), (b'Find & treat', b'Find & treat'), (b'Prison screening', b'Prison screening'), (b'Port Health/HPA', b'Port Health/HPA'), (b'Private', b'Private')], default=b'', max_length=256),
        ),
    ]

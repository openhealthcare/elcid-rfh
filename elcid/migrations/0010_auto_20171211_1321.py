# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0009_auto_20171107_2248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demographics',
            name='date_of_birth',
            field=models.DateField(null=True, verbose_name=b'Date of Birth', blank=True),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='date_of_death',
            field=models.DateField(null=True, verbose_name=b'Date of Death', blank=True),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='death_indicator',
            field=models.BooleanField(default=False, help_text=b'This field will be True if the patient is deceased.'),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='gp_practice_code',
            field=models.CharField(max_length=20, null=True, verbose_name=b'GP Practice Code', blank=True),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='hospital_number',
            field=models.CharField(help_text=b'The unique identifier for this patient at the hospital.', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='nhs_number',
            field=models.CharField(max_length=255, null=True, verbose_name=b'NHS Number', blank=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0012_maritalstatus_title'),
        ('elcid', '0041_auto_20160229_1518'),
    ]

    operations = [
        migrations.RenameField(
            model_name='demographics',
            old_name='ethnicity',
            new_name='ethnicity_old',
        ),
        migrations.AddField(
            model_name='demographics',
            name='date_of_death',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='first_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='gp_practice_code',
            field=models.CharField(max_length=20, blank=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='middle_name',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='post_code',
            field=models.CharField(max_length=20, blank=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='sex_fk',
            field=models.ForeignKey(blank=True, to='opal.Gender', null=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='sex_ft',
            field=models.CharField(default=b'', max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='sourced_from_upstream',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='demographics',
            name='surname',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='title_fk',
            field=models.ForeignKey(blank=True, to='opal.Title', null=True),
        ),
        migrations.AddField(
            model_name='demographics',
            name='title_ft',
            field=models.CharField(default=b'', max_length=255, null=True, blank=True),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-03-14 11:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0021_pastmedicalhistory'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='referralroute',
            name='internal',
        ),
        migrations.RemoveField(
            model_name='referralroute',
            name='referral_name',
        ),
        migrations.RemoveField(
            model_name='referralroute',
            name='referral_organisation_fk',
        ),
        migrations.RemoveField(
            model_name='referralroute',
            name='referral_organisation_ft',
        ),
        migrations.RemoveField(
            model_name='referralroute',
            name='referral_team_fk',
        ),
        migrations.RemoveField(
            model_name='referralroute',
            name='referral_team_ft',
        ),
        migrations.RemoveField(
            model_name='referralroute',
            name='referral_type_fk',
        ),
        migrations.RemoveField(
            model_name='referralroute',
            name='referral_type_ft',
        ),
        migrations.AddField(
            model_name='referralroute',
            name='referral_type',
            field=models.CharField(blank=True, choices=[(b'Primary care (GP)', b'Primary care (GP)'), (b'Primary care (other)', b'Primary care (other)')], default=b'', max_length=256),
        ),
    ]

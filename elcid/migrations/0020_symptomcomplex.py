# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-01-29 23:23
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import opal.models


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0034_auto_20171214_1845'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('elcid', '0019_referralroute'),
    ]

    operations = [
        migrations.CreateModel(
            name='SymptomComplex',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('updated', models.DateTimeField(blank=True, null=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('duration', models.CharField(blank=True, choices=[(b'3 days or less', b'3 days or less'), (b'4-10 days', b'4-10 days'), (b'11-21 days', b'11-21 days'), (b'22 days to 3 months', b'22 days to 3 months'), (b'over 3 months', b'over 3 months')], help_text=b'The duration for which the patient had been experiencing these symptoms when recorded.', max_length=255, null=True)),
                ('details', models.TextField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_elcid_symptomcomplex_subrecords', to=settings.AUTH_USER_MODEL)),
                ('episode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode')),
                ('symptoms', models.ManyToManyField(blank=True, related_name='symptoms', to='opal.Symptom')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_elcid_symptomcomplex_subrecords', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
                'verbose_name_plural': 'Symptom complexes',
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0007_auto_20160927_0931'),
    ]

    operations = [
        migrations.CreateModel(
            name='BloodCultureSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='bloodculture',
            name='source_fk',
            field=models.ForeignKey(blank=True, to='elcid.BloodCultureSource', null=True),
        ),
    ]

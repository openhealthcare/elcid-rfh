# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lab', '__first__'),
        ('elcid', '0006_auto_20160921_1357'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Organism',
        ),
        migrations.CreateModel(
            name='OrganismTest',
            fields=[
            ],
            options={
                'verbose_name': 'Organism',
                'proxy': True,
            },
            bases=('lab.labtest',),
        ),
        migrations.AlterModelOptions(
            name='gnr',
            options={'verbose_name': 'GNR'},
        ),
        migrations.AlterModelOptions(
            name='gpcstaph',
            options={'verbose_name': 'GPC Staph'},
        ),
        migrations.AlterModelOptions(
            name='gpcstrep',
            options={'verbose_name': 'GPC Strep'},
        ),
        migrations.AlterModelOptions(
            name='quickfish',
            options={'verbose_name': 'QuickFISH'},
        ),
        migrations.AlterField(
            model_name='bloodculture',
            name='source_fk',
            field=models.ForeignKey(blank=True, to='opal.Line_type', null=True),
        ),
        migrations.DeleteModel(
            name='BloodCultureSource',
        ),
    ]

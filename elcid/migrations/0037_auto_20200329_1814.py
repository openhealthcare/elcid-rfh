# Generated by Django 2.0.13 on 2020-03-29 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0036_auto_20200328_1524'),
    ]

    operations = [
        migrations.AlterField(
            model_name='icuround',
            name='fio2',
            field=models.FloatField(blank=True, null=True, verbose_name='FiO₂'),
        ),
        migrations.AlterField(
            model_name='icuround',
            name='meld_score',
            field=models.FloatField(blank=True, null=True, verbose_name='MELD score'),
        ),
        migrations.AlterField(
            model_name='icuround',
            name='sofa_score',
            field=models.FloatField(blank=True, null=True, verbose_name='SOFA score'),
        ),
    ]

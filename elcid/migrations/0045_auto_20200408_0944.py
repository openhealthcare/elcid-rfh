# Generated by Django 2.0.9 on 2020-04-08 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0044_auto_20200407_1309'),
    ]

    operations = [
        migrations.AlterField(
            model_name='icuadmission',
            name='apache2_score',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='APACHE II Score'),
        ),
    ]

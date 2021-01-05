# Generated by Django 2.0.13 on 2021-01-05 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('covid', '0052_auto_20210105_1455'),
    ]

    operations = [
        migrations.AddField(
            model_name='covidadmission',
            name='days_on_optiflow',
            field=models.IntegerField(blank=True, null=True, verbose_name='Total Number Of Days On Optiflow'),
        ),
        migrations.AddField(
            model_name='covidadmission',
            name='other_drugs',
            field=models.TextField(blank=True, null=True),
        ),
    ]

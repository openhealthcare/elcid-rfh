# Generated by Django 2.0.13 on 2021-05-11 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admissions', '0007_auto_20210511_1030'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transferhistory',
            name='spell_number',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
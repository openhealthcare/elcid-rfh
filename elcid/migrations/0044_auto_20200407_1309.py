# Generated by Django 2.0.9 on 2020-04-07 13:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0043_auto_20200407_1308'),
    ]

    operations = [
        migrations.RenameField(
            model_name='icuround',
            old_name='inotropic_dose',
            new_name='inotrope_dose',
        ),
        migrations.RenameField(
            model_name='icuround',
            old_name='inotropic_drug_fk',
            new_name='inotrope_fk',
        ),
        migrations.RenameField(
            model_name='icuround',
            old_name='inotropic_drug_ft',
            new_name='inotrope_ft',
        ),
    ]

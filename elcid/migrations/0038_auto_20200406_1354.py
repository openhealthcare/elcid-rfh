# Generated by Django 2.0.9 on 2020-04-06 13:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0037_auto_20200329_1814'),
    ]

    operations = [
        migrations.RenameField(
            model_name='icuadmission',
            old_name='apache_score',
            new_name='apache2_score',
        ),
    ]

# Generated by Django 2.0.13 on 2019-04-23 18:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0030_auto_20190423_1743'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bloodcultureisolate',
            name='gnr_fk',
        ),
        migrations.RemoveField(
            model_name='bloodcultureisolate',
            name='gnr_ft',
        ),
    ]

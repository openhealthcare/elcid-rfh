# Generated by Django 2.2.16 on 2023-05-10 07:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0069_blood_culture_updated_created'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bloodcultureisolate',
            name='created',
        ),
        migrations.RemoveField(
            model_name='bloodcultureisolate',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='bloodcultureisolate',
            name='updated',
        ),
        migrations.RemoveField(
            model_name='bloodcultureisolate',
            name='updated_by',
        ),
    ]

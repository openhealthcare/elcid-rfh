# Generated by Django 2.2.16 on 2023-03-17 09:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0006_appointment_created'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appointment',
            old_name='aiL_location_resource_id',
            new_name='ail_location_resource_id',
        ),
    ]

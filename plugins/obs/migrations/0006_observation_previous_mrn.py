# Generated by Django 2.2.16 on 2023-03-10 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('obs', '0005_auto_20230310_1712'),
    ]

    operations = [
        migrations.AddField(
            model_name='observation',
            name='previous_mrn',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
# Generated by Django 2.0.13 on 2021-07-30 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rnoh', '0005_auto_20210730_1157'),
    ]

    operations = [
        migrations.AddField(
            model_name='rnohmicrobiology',
            name='test_name',
            field=models.CharField(blank=True, choices=[('Culture', 'Culture'), ('MRSA Screen', 'MRSA Screen'), ('CPE Screen', 'CPE Screen')], max_length=200, null=True),
        ),
    ]

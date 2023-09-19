# Generated by Django 2.0.13 on 2023-09-19 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipc', '0010_auto_20230914_0853'),
    ]

    operations = [
        migrations.AddField(
            model_name='ipcstatus',
            name='acinetobacter_lab_numbers',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ipcstatus',
            name='c_difficile_lab_numbers',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ipcstatus',
            name='candida_auris_lab_numbers',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ipcstatus',
            name='carb_resistance_lab_numbers',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ipcstatus',
            name='cjd_lab_numbers',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ipcstatus',
            name='mrsa_lab_numbers',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ipcstatus',
            name='mrsa_neg_lab_numbers',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ipcstatus',
            name='multi_drug_resistant_organism_lab_numbers',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ipcstatus',
            name='reactive_lab_numbers',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ipcstatus',
            name='vre_lab_numbers',
            field=models.TextField(blank=True, null=True),
        ),
    ]

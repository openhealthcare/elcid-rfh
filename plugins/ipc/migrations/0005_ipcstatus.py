# Generated by Django 2.2.16 on 2021-12-13 19:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import opal.models


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0040_auto_20201007_1346'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ipc', '0004_auto_20210511_1115'),
    ]

    operations = [
        migrations.CreateModel(
            name='IPCStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, null=True, verbose_name='Created')),
                ('updated', models.DateTimeField(blank=True, null=True, verbose_name='Updated')),
                ('consistency_token', models.CharField(max_length=8, verbose_name='Consistency Token')),
                ('mrsa', models.BooleanField(default=False, verbose_name='MRSA')),
                ('mrsa_date', models.DateField(blank=True, null=True, verbose_name='MRSA Date')),
                ('mrsa_neg', models.BooleanField(default=False, verbose_name='MRSA Neg')),
                ('mrsa_neg_date', models.DateField(blank=True, null=True, verbose_name='MRSA Neg Date')),
                ('reactive', models.BooleanField(default=False)),
                ('reactive_date', models.DateField(blank=True, null=True)),
                ('c_difficile', models.BooleanField(default=False)),
                ('c_difficile_date', models.DateField(blank=True, null=True)),
                ('vre', models.BooleanField(default=False, verbose_name='VRE')),
                ('vre_date', models.DateField(blank=True, null=True, verbose_name='VRE Date')),
                ('vre_neg', models.BooleanField(default=False, verbose_name='VRE Neg')),
                ('vre_neg_date', models.DateField(blank=True, null=True, verbose_name='VRE Neg Date')),
                ('carb_resistance', models.BooleanField(default=False)),
                ('carb_resistance_date', models.DateField(blank=True, null=True)),
                ('contact_of_carb_resistance', models.BooleanField(default=False)),
                ('contact_of_carb_resistance_date', models.DateField(blank=True, null=True)),
                ('acinetobacter', models.BooleanField(default=False)),
                ('acinetobacter_date', models.DateField(blank=True, null=True)),
                ('contact_of_acinetobacter', models.BooleanField(default=False)),
                ('contact_of_acinetobacter_date', models.DateField(blank=True, null=True)),
                ('cjd', models.BooleanField(default=False, verbose_name='CJD')),
                ('cjd_date', models.DateField(blank=True, null=True, verbose_name='CJD Date')),
                ('candida_auris', models.BooleanField(default=False)),
                ('candida_auris_date', models.DateField(blank=True, null=True)),
                ('contact_of_candida_auris', models.BooleanField(default=False)),
                ('contact_of_candida_auris_date', models.DateField(blank=True, null=True)),
                ('multi_drug_resistant_organism', models.BooleanField(default=False)),
                ('multi_drug_resistant_organism_date', models.DateField(blank=True, null=True)),
                ('covid_19', models.BooleanField(default=False, verbose_name='Covid-19')),
                ('covid_19_date', models.DateField(blank=True, null=True, verbose_name='Covid-19 Date')),
                ('contact_of_covid_19', models.BooleanField(default=False, verbose_name='Contact of Covid-19')),
                ('contact_of_covid_19_date', models.DateField(blank=True, null=True, verbose_name='Contact of Covid-19 Date')),
                ('other', models.CharField(blank=True, max_length=256, null=True)),
                ('other_date', models.DateField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_ipc_ipcstatus_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_ipc_ipcstatus_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By')),
            ],
            options={
                'verbose_name': 'IPC Portal Status',
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
    ]

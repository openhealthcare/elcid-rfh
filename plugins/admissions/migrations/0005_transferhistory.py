# Generated by Django 2.0.13 on 2021-04-22 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admissions', '0004_upstreamlocation'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransferHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('encounter_slice_id', models.IntegerField(blank=True, null=True)),
                ('update_datetime', models.DateTimeField(blank=True, null=True)),
                ('active_transfer', models.IntegerField(blank=True, null=True)),
                ('active_spell', models.IntegerField(blank=True, null=True)),
                ('encounter_id', models.IntegerField(blank=True, null=True)),
                ('transfer_sequence_number', models.IntegerField(blank=True, null=True)),
                ('active_transfer_sequence_number', models.IntegerField(blank=True, null=True)),
                ('transfer_start_datetime', models.DateTimeField(blank=True, null=True)),
                ('transfer_end_datetime', models.DateTimeField(blank=True, null=True)),
                ('transfer_location_code', models.IntegerField(blank=True, null=True)),
                ('site_code', models.CharField(blank=True, max_length=255, null=True)),
                ('unit', models.CharField(blank=True, max_length=255, null=True)),
                ('room', models.CharField(blank=True, max_length=255, null=True)),
                ('bed', models.CharField(blank=True, max_length=255, null=True)),
                ('transfer_reason', models.CharField(blank=True, max_length=255, null=True)),
                ('created_datetime', models.DateTimeField(blank=True, null=True)),
                ('updated_datetime', models.DateTimeField(blank=True, null=True)),
                ('trf_inp_th_encntr_updt_dt_tm', models.DateTimeField(blank=True, null=True)),
                ('trf_inp_th_encntr_slice_updt_dt_tm', models.DateTimeField(blank=True, null=True)),
                ('trf_inp_th_encntr_alias_updt_dt_tm', models.DateTimeField(blank=True, null=True)),
                ('trf_inp_th_encntr_slice_act_updt_dt_tm', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]

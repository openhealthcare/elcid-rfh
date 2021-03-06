# Generated by Django 2.0.9 on 2020-02-14 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='appointment_id',
            field=models.CharField(blank=True, help_text='Unique appointment identifier', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='derived_appointment_location_site',
            field=models.CharField(blank=True, help_text='Cleaned up Appointment location Site (taken from AIL)', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='duration',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='duration_units',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='encounter_number',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='filler_appointment_id',
            field=models.CharField(blank=True, help_text='Choose & Book ID when relevent', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='hl7_message_id',
            field=models.CharField(blank=True, help_text='Appointment HL7 ID', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='hl7_message_type',
            field=models.CharField(blank=True, help_text='Appointment HL7 message type', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='hospital_service',
            field=models.CharField(blank=True, help_text='Speciality code associated with the encounter', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='patient_number',
            field=models.CharField(blank=True, help_text='MRN', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='status_code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='tci_datetime_text',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='v_account_status',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='v_attending_doctor_code',
            field=models.CharField(blank=True, help_text='Encounter consultant', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='v_attending_doctor_name',
            field=models.CharField(blank=True, help_text='Encounter consultant', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='v_patient_class',
            field=models.CharField(blank=True, help_text='Encounter Patient Class', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='v_patient_forename',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='v_patient_nhs_number',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='v_patient_number',
            field=models.CharField(blank=True, help_text='MRN', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='v_patient_surname',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='v_patient_type',
            field=models.CharField(blank=True, help_text='Encounter Patient Type', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='v_referring_doctor_code',
            field=models.CharField(blank=True, help_text='Encounter referring doctor', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='v_referring_doctor_name',
            field=models.CharField(blank=True, help_text='Encounter referring doctor', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='visit_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]

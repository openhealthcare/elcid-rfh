# Generated by Django 2.0.9 on 2020-02-14 11:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('opal', '0037_auto_20181114_1445'),
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('v_patient_number', models.CharField(blank=True, help_text='MRN', max_length=20, null=True)),
                ('v_patient_nhs_number', models.CharField(blank=True, max_length=20, null=True)),
                ('v_patient_surname', models.CharField(blank=True, max_length=20, null=True)),
                ('v_patient_forename', models.CharField(blank=True, max_length=20, null=True)),
                ('v_patient_dob', models.DateTimeField(blank=True, null=True)),
                ('patient_number', models.CharField(blank=True, help_text='MRN', max_length=20, null=True)),
                ('v_patient_class', models.CharField(blank=True, help_text='Encounter Patient Class', max_length=50, null=True)),
                ('v_attending_doctor_code', models.CharField(blank=True, help_text='Encounter consultant', max_length=50, null=True)),
                ('v_attending_doctor_name', models.CharField(blank=True, help_text='Encounter consultant', max_length=50, null=True)),
                ('v_referring_doctor_code', models.CharField(blank=True, help_text='Encounter referring doctor', max_length=50, null=True)),
                ('v_referring_doctor_name', models.CharField(blank=True, help_text='Encounter referring doctor', max_length=50, null=True)),
                ('v_patient_type', models.CharField(blank=True, help_text='Encounter Patient Type', max_length=50, null=True)),
                ('v_account_status', models.CharField(blank=True, max_length=50, null=True)),
                ('hl7_message_type', models.CharField(blank=True, help_text='Appointment HL7 message type', max_length=50, null=True)),
                ('hl7_message_date', models.DateTimeField(blank=True, help_text='Appointment HL7 Date', null=True)),
                ('hl7_message_id', models.CharField(blank=True, help_text='Appointment HL7 ID', max_length=50, null=True)),
                ('sqlserver_id', models.IntegerField(blank=True, help_text='Internal SQL Appointment Primary Key', null=True)),
                ('insert_date', models.DateTimeField(blank=True, help_text='Datetime inserted into the database', null=True)),
                ('last_updated', models.DateTimeField(blank=True, help_text='Datetime last updated on the database', null=True)),
                ('aig_resource_id', models.CharField(blank=True, help_text='General Resourse associated with non-consultant seeing the patient eg SPR, Nurse, Therapist', max_length=255, null=True)),
                ('aiL_location_resource_id', models.CharField(blank=True, help_text='Actual location of the appointment', max_length=255, null=True)),
                ('aip_personnel_id', models.CharField(blank=True, help_text='Consultant resource details if they are seeing the patient.', max_length=255, null=True)),
                ('tci_datetime_text', models.CharField(blank=True, max_length=50, null=True)),
                ('tci_datetime', models.DateTimeField(blank=True, null=True)),
                ('tci_location', models.CharField(blank=True, max_length=255, null=True)),
                ('encounter_number', models.CharField(blank=True, max_length=50, null=True)),
                ('visit_id', models.CharField(blank=True, max_length=50, null=True)),
                ('appointment_id', models.CharField(blank=True, help_text='Unique appointment identifier', max_length=50, null=True)),
                ('filler_appointment_id', models.CharField(blank=True, help_text='Choose & Book ID when relevent', max_length=50, null=True)),
                ('full_appointment_type', models.CharField(blank=True, help_text='Raw Appointment Type', max_length=255, null=True)),
                ('duration', models.CharField(blank=True, max_length=50, null=True)),
                ('duration_units', models.CharField(blank=True, max_length=50, null=True)),
                ('start_datetime', models.DateTimeField(blank=True, null=True)),
                ('end_datetime', models.DateTimeField(blank=True, null=True)),
                ('full_contact_person', models.CharField(blank=True, max_length=255, null=True)),
                ('full_entered_by_person', models.CharField(blank=True, max_length=255, null=True)),
                ('status_code', models.CharField(blank=True, max_length=50, null=True)),
                ('hospital_service', models.CharField(blank=True, help_text='Speciality code associated with the encounter', max_length=50, null=True)),
                ('derived_appointment_type', models.CharField(blank=True, help_text='Cleaned up Appointment type (Taken from Full Appointment type)', max_length=100, null=True)),
                ('derived_appointment_location', models.CharField(blank=True, help_text='Cleaned up Appointment location (taken from AIL)', max_length=255, null=True)),
                ('derived_appointment_location_site', models.CharField(blank=True, help_text='Cleaned up Appointment location Site (taken from AIL)', max_length=20, null=True)),
                ('derived_clinic_resource', models.CharField(blank=True, help_text='Cleaned up Resource (taken from AIL & AIP) AIP taken presedence', max_length=255, null=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='opal.Patient')),
            ],
        ),
    ]

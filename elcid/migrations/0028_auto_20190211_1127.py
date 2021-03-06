# Generated by Django 2.0.9 on 2019-02-11 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0027_auto_20190124_2114'),
    ]

    operations = [
        migrations.AddField(
            model_name='bloodculturesource',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='bloodculturesource',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='bloodculturesource',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='consultant',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='consultant',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='consultant',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='drug_delivered',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='drug_delivered',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='drug_delivered',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='imagingtypes',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='imagingtypes',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='imagingtypes',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='infectionsource',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='infectionsource',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='infectionsource',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='iv_stop',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='iv_stop',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='iv_stop',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='liverfunction',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='liverfunction',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='liverfunction',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='locationcategory',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='locationcategory',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='locationcategory',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='primarydiagnosiscondition',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='primarydiagnosiscondition',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='primarydiagnosiscondition',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='provenance',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='provenance',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='provenance',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='renalfunction',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='renalfunction',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='renalfunction',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='antimicrobial',
            name='adverse_event_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='antimicrobial',
            name='delivered_by_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='antimicrobial',
            name='drug_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='antimicrobial',
            name='frequency_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='antimicrobial',
            name='reason_for_stopping_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='antimicrobial',
            name='route_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='birth_place_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True, verbose_name='Date of Birth'),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='date_of_death',
            field=models.DateField(blank=True, null=True, verbose_name='Date of Death'),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='death_indicator',
            field=models.BooleanField(default=False, help_text='This field will be True if the patient is deceased.'),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='ethnicity_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='gp_practice_code',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='GP Practice Code'),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='hospital_number',
            field=models.CharField(blank=True, help_text='The unique identifier for this patient at the hospital.', max_length=255),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='marital_status_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='nhs_number',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='NHS Number'),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='sex_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='demographics',
            name='title_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='diagnosis',
            name='condition_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='diagnosis',
            name='provisional',
            field=models.BooleanField(default=False, help_text='True if the diagnosis is provisional. Defaults to False', verbose_name='Provisional?'),
        ),
        migrations.AlterField(
            model_name='finaldiagnosis',
            name='hcai_related',
            field=models.BooleanField(default=False, verbose_name='HCAI related'),
        ),
        migrations.AlterField(
            model_name='imaging',
            name='imaging_type_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='infection',
            name='source_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='line',
            name='complications_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='line',
            name='line_type_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='line',
            name='removal_reason_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='line',
            name='site_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='category_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='hospital_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='provenance_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='ward_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='microbiologyinput',
            name='liver_function_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='microbiologyinput',
            name='reason_for_interaction_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='microbiologyinput',
            name='renal_function_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='pastmedicalhistory',
            name='condition_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='primarydiagnosis',
            name='condition_ft',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='referralroute',
            name='referral_reason',
            field=models.CharField(blank=True, choices=[('Symptomatic', 'Symptomatic'), ('TB contact screening', 'TB contact screening'), ('New entract screening', 'New entract screening'), ('Transferred in TB Rx', 'Transferred in TB Rx'), ('Immunosuppressant', 'Immunosuppressant'), ('BCG Vaccination', 'BCG Vaccination'), ('Other', 'Other')], default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='referralroute',
            name='referral_type',
            field=models.CharField(blank=True, choices=[('Primary care (GP)', 'Primary care (GP)'), ('Primary care (other)', 'Primary care (other)'), ('Secondary care', 'Secondary care'), ('TB service', 'TB service'), ('A&E', 'A&E'), ('Find & treat', 'Find & treat'), ('Prison screening', 'Prison screening'), ('Port Health/HPA', 'Port Health/HPA'), ('Private', 'Private')], default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='symptomcomplex',
            name='duration',
            field=models.CharField(blank=True, choices=[('3 days or less', '3 days or less'), ('4-10 days', '4-10 days'), ('11-21 days', '11-21 days'), ('22 days to 3 months', '22 days to 3 months'), ('over 3 months', 'over 3 months')], help_text='The duration for which the patient had been experiencing these symptoms when recorded.', max_length=255, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='bloodculturesource',
            unique_together={('code', 'system')},
        ),
        migrations.AlterUniqueTogether(
            name='consultant',
            unique_together={('code', 'system')},
        ),
        migrations.AlterUniqueTogether(
            name='imagingtypes',
            unique_together={('code', 'system')},
        ),
        migrations.AlterUniqueTogether(
            name='infectionsource',
            unique_together={('code', 'system')},
        ),
        migrations.AlterUniqueTogether(
            name='liverfunction',
            unique_together={('code', 'system')},
        ),
        migrations.AlterUniqueTogether(
            name='locationcategory',
            unique_together={('code', 'system')},
        ),
        migrations.AlterUniqueTogether(
            name='primarydiagnosiscondition',
            unique_together={('code', 'system')},
        ),
        migrations.AlterUniqueTogether(
            name='provenance',
            unique_together={('code', 'system')},
        ),
        migrations.AlterUniqueTogether(
            name='renalfunction',
            unique_together={('code', 'system')},
        ),
    ]

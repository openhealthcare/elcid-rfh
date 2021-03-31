# Generated by Django 2.0.13 on 2021-03-29 11:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tb', '0049_mantouxtest_date_administered'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accessconsiderations',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='accessconsiderations',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='accessconsiderations',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_accessconsiderations_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='accessconsiderations',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='accessconsiderations',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='accessconsiderations',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_accessconsiderations_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='adversereaction',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='adversereaction',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='adversereaction',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_adversereaction_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='adversereaction',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode', verbose_name='Episode'),
        ),
        migrations.AlterField(
            model_name='adversereaction',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='adversereaction',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_adversereaction_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='allergies',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='allergies',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='allergies',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_allergies_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='allergies',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='allergies',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='allergies',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_allergies_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='bcg',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='bcg',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='bcg',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_bcg_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='bcg',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='bcg',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='bcg',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_bcg_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='communinicationconsiderations',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='communinicationconsiderations',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='communinicationconsiderations',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_communinicationconsiderations_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='communinicationconsiderations',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='communinicationconsiderations',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='communinicationconsiderations',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_communinicationconsiderations_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='contactdetails',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='contactdetails',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='contactdetails',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_contactdetails_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='contactdetails',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='contactdetails',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='contactdetails',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_contactdetails_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='employment',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='employment',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='employment',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_employment_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='employment',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='employment',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='employment',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_employment_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='indexcase',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='indexcase',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='indexcase',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_indexcase_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='indexcase',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='indexcase',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='indexcase',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_indexcase_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='lymphnodeswellingsite',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='lymphnodeswellingsite',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='lymphnodeswellingsite',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_lymphnodeswellingsite_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='lymphnodeswellingsite',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode', verbose_name='Episode'),
        ),
        migrations.AlterField(
            model_name='lymphnodeswellingsite',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='lymphnodeswellingsite',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_lymphnodeswellingsite_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='lymphnodeswellingsiteoptions',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Code'),
        ),
        migrations.AlterField(
            model_name='lymphnodeswellingsiteoptions',
            name='name',
            field=models.CharField(max_length=255, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='lymphnodeswellingsiteoptions',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='System'),
        ),
        migrations.AlterField(
            model_name='lymphnodeswellingsiteoptions',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Version'),
        ),
        migrations.AlterField(
            model_name='mantouxtest',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='mantouxtest',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='mantouxtest',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_mantouxtest_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='mantouxtest',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='mantouxtest',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='mantouxtest',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_mantouxtest_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='nationality',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='nationality',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='nationality',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_nationality_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='nationality',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='nationality',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='nationality',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_nationality_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='nextofkin',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='nextofkin',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='nextofkin',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_nextofkin_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='nextofkin',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='nextofkin',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='nextofkin',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_nextofkin_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='otherinvestigation',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='otherinvestigation',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='otherinvestigation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_otherinvestigation_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='otherinvestigation',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode', verbose_name='Episode'),
        ),
        migrations.AlterField(
            model_name='otherinvestigation',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='otherinvestigation',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_otherinvestigation_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='patientconsultation',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='patientconsultation',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='patientconsultation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_patientconsultation_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='patientconsultation',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode', verbose_name='Episode'),
        ),
        migrations.AlterField(
            model_name='patientconsultation',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='patientconsultation',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_patientconsultation_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='pregnancy',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='pregnancy',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='pregnancy',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_pregnancy_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='pregnancy',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='pregnancy',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='pregnancy',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_pregnancy_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='recreationaldrug',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Code'),
        ),
        migrations.AlterField(
            model_name='recreationaldrug',
            name='name',
            field=models.CharField(max_length=255, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='recreationaldrug',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='System'),
        ),
        migrations.AlterField(
            model_name='recreationaldrug',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Version'),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_socialhistory_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode', verbose_name='Episode'),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_socialhistory_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='tbcasemanager',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Code'),
        ),
        migrations.AlterField(
            model_name='tbcasemanager',
            name='name',
            field=models.CharField(max_length=255, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='tbcasemanager',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='System'),
        ),
        migrations.AlterField(
            model_name='tbcasemanager',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Version'),
        ),
        migrations.AlterField(
            model_name='tbhistory',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='tbhistory',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='tbhistory',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_tbhistory_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='tbhistory',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient', verbose_name='Patient'),
        ),
        migrations.AlterField(
            model_name='tbhistory',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='tbhistory',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_tbhistory_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='tblocation',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='tblocation',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='tblocation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_tblocation_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='tblocation',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode', verbose_name='Episode'),
        ),
        migrations.AlterField(
            model_name='tblocation',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='tblocation',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_tblocation_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='tbmanagement',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='tbmanagement',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='tbmanagement',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_tbmanagement_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='tbmanagement',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode', verbose_name='Episode'),
        ),
        migrations.AlterField(
            model_name='tbmanagement',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='tbmanagement',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_tbmanagement_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='tbmeta',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='tbmeta',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='tbmeta',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_tbmeta_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='tbmeta',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode', verbose_name='Episode'),
        ),
        migrations.AlterField(
            model_name='tbmeta',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='tbmeta',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_tbmeta_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='tbsite',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Code'),
        ),
        migrations.AlterField(
            model_name='tbsite',
            name='name',
            field=models.CharField(max_length=255, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='tbsite',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='System'),
        ),
        migrations.AlterField(
            model_name='tbsite',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Version'),
        ),
        migrations.AlterField(
            model_name='tbtreatmentcentre',
            name='code',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Code'),
        ),
        migrations.AlterField(
            model_name='tbtreatmentcentre',
            name='name',
            field=models.CharField(max_length=255, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='tbtreatmentcentre',
            name='system',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='System'),
        ),
        migrations.AlterField(
            model_name='tbtreatmentcentre',
            name='version',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Version'),
        ),
        migrations.AlterField(
            model_name='travel',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='travel',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='travel',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_travel_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='travel',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode', verbose_name='Episode'),
        ),
        migrations.AlterField(
            model_name='travel',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='travel',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_travel_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
        migrations.AlterField(
            model_name='treatment',
            name='consistency_token',
            field=models.CharField(max_length=8, verbose_name='Consistency Token'),
        ),
        migrations.AlterField(
            model_name='treatment',
            name='created',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='treatment',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_treatment_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='treatment',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode', verbose_name='Episode'),
        ),
        migrations.AlterField(
            model_name='treatment',
            name='updated',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Updated'),
        ),
        migrations.AlterField(
            model_name='treatment',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_treatment_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By'),
        ),
    ]
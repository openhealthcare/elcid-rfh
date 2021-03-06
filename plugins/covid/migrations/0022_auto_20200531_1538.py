# Generated by Django 2.0.13 on 2020-05-31 15:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import opal.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('opal', '0037_auto_20181114_1445'),
        ('covid', '0021_auto_20200528_1314'),
    ]

    operations = [
        migrations.CreateModel(
            name='CovidFollowupActions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('updated', models.DateTimeField(blank=True, null=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('cxr', models.NullBooleanField(verbose_name='CXR')),
                ('ecg', models.NullBooleanField(verbose_name='ECG')),
                ('echocardiogram', models.NullBooleanField()),
                ('ct_chest', models.NullBooleanField(verbose_name='CT Chest')),
                ('pft', models.NullBooleanField(verbose_name='PFT')),
                ('exercise', models.NullBooleanField(verbose_name='Exercise Testing')),
                ('repeat_bloods', models.NullBooleanField()),
                ('other_investigations', models.CharField(blank=True, max_length=255, null=True)),
                ('anticoagulation', models.NullBooleanField()),
                ('cardiology', models.NullBooleanField()),
                ('elderly_care', models.NullBooleanField()),
                ('fatigue_services', models.NullBooleanField()),
                ('hepatology', models.NullBooleanField()),
                ('neurology', models.NullBooleanField()),
                ('primary_care', models.NullBooleanField()),
                ('psychology', models.NullBooleanField()),
                ('psychiatry', models.NullBooleanField()),
                ('respiratory', models.NullBooleanField()),
                ('rehabilitation', models.NullBooleanField()),
                ('other_referral', models.CharField(blank=True, max_length=255, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_covid_covidfollowupactions_subrecords', to=settings.AUTH_USER_MODEL)),
                ('episode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_covid_covidfollowupactions_subrecords', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
        migrations.RemoveField(
            model_name='covidfollowupcall',
            name='diabetic_team',
        ),
        migrations.RemoveField(
            model_name='covidfollowupcall',
            name='haem_clinic',
        ),
        migrations.RemoveField(
            model_name='covidfollowupcall',
            name='psych_referral',
        ),
        migrations.RemoveField(
            model_name='covidfollowupcall',
            name='unable_to_complete',
        ),
        migrations.RemoveField(
            model_name='covidfollowupcall',
            name='unreachable',
        ),
        migrations.AlterField(
            model_name='covidfollowupcall',
            name='follow_up_outcome',
            field=models.CharField(blank=True, choices=[('Unreachable', 'Unreachable'), ('Unable to complete', 'Unable to complete'), ('Further Follow UpDischarge', 'Further Follow UpDischarge')], max_length=50, null=True),
        ),
    ]

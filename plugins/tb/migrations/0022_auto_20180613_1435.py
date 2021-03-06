# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-06-13 14:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import opal.models


class Migration(migrations.Migration):

    dependencies = [
        ('opal', '0034_auto_20171214_1845'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tb', '0021_auto_20180515_1445'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessConsiderations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('updated', models.DateTimeField(blank=True, null=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('mobility_problem', models.BooleanField(default=False)),
                ('needs_help_with_transport', models.BooleanField(default=False)),
                ('provision', models.BooleanField(default=False)),
                ('finance', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_accessconsiderations_subrecords', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_accessconsiderations_subrecords', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Access & Transport',
                'verbose_name_plural': 'Access Considerations',
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
        migrations.CreateModel(
            name='CommuninicationConsiderations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('updated', models.DateTimeField(blank=True, null=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('needs_an_interpreter', models.BooleanField(default=False)),
                ('language', models.CharField(blank=True, max_length=256)),
                ('sensory_impairment', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_communinicationconsiderations_subrecords', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_communinicationconsiderations_subrecords', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Communication',
                'verbose_name_plural': 'Communinication Considerations',
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Employment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('updated', models.DateTimeField(blank=True, null=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('occupation', models.TextField(blank=True, null=True)),
                ('financial_status', models.CharField(choices=[(b'Nil income', b'Nil income'), (b'On benefits', b'On benefits'), (b'Other(SS/NASS)', b'Other(SS/NASS)'), (b'Employed', b'Employed')], max_length=256)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_employment_subrecords', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_employment_subrecords', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Immigration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('updated', models.DateTimeField(blank=True, null=True)),
                ('consistency_token', models.CharField(max_length=8)),
                ('immigration_concerns', models.BooleanField(default=False)),
                ('immigration_details', models.TextField(blank=True)),
                ('immigration_support_officer', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tb_immigration_subrecords', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_tb_immigration_subrecords', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
        migrations.RemoveField(
            model_name='socialhistory',
            name='alcohol_dependent',
        ),
        migrations.RemoveField(
            model_name='socialhistory',
            name='occupation',
        ),
        migrations.AddField(
            model_name='socialhistory',
            name='community_nurse',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name=b'CPN/CMHT'),
        ),
        migrations.AddField(
            model_name='socialhistory',
            name='drug_community_worker',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name=b'Drug/alcohol worker'),
        ),
        migrations.AddField(
            model_name='socialhistory',
            name='history_of_alocohol_dependence',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='socialhistory',
            name='immigration_concerns',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='socialhistory',
            name='immigration_concerns_details',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='socialhistory',
            name='mental_health_issues',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='socialhistory',
            name='opiate_replacement_therapy',
            field=models.BooleanField(default=False, verbose_name=b'on opiate replacement therapy'),
        ),
        migrations.AddField(
            model_name='socialhistory',
            name='probation_officer',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='homelessness_type',
            field=models.CharField(blank=True, choices=[(b'Hostel', b'Hostel'), (b'Sofa surfing', b'Sofa surfing'), (b'Street', b'Street'), (b'Other', b'Other')], max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='prison_history',
            field=models.CharField(blank=True, choices=[(b'Never', b'Never'), (b'Current', b'Current'), (b'Within the last 5 years', b'Within the last 5 years'), (b'Over 5 years ago', b'Over 5 years ago')], max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='recreational_drug_use',
            field=models.CharField(blank=True, choices=[(b'Never', b'Never'), (b'Current', b'Current'), (b'Dependent', b'Dependent'), (b'Past', b'Past')], max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='socialhistory',
            name='smoking',
            field=models.CharField(blank=True, choices=[(b'Never', b'Never'), (b'Current', b'Current'), (b'Past', b'Past')], max_length=250, null=True),
        ),
    ]

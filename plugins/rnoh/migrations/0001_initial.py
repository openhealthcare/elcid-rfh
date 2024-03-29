# Generated by Django 2.0.13 on 2021-07-26 07:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import opal.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('opal', '0040_auto_20201007_1346'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OPATOutcomes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, null=True, verbose_name='Created')),
                ('updated', models.DateTimeField(blank=True, null=True, verbose_name='Updated')),
                ('consistency_token', models.CharField(max_length=8, verbose_name='Consistency Token')),
                ('outcome_early', models.CharField(blank=True, choices=[('Cured', 'Cured'), ('Improved - off antibiotics', 'Improved - off antibiotics'), ('Improved - on suppression', 'Improved - on suppression'), ('Improved - further treatment planned', 'Improved - further treatment planned'), ('Failed', 'Failed')], max_length=200, null=True)),
                ('outcome_early_date', models.DateField(blank=True, null=True)),
                ('outcome_one_year', models.CharField(blank=True, choices=[('Cured', 'Cured'), ('Improved - off antibiotics', 'Improved - off antibiotics'), ('Improved - on suppression', 'Improved - on suppression'), ('Improved - further treatment planned', 'Improved - further treatment planned'), ('Failed', 'Failed')], max_length=200, null=True)),
                ('outcome_one_year_date', models.DateField(blank=True, null=True)),
                ('outcome_two_years', models.CharField(blank=True, choices=[('Cured', 'Cured'), ('Improved - off antibiotics', 'Improved - off antibiotics'), ('Improved - on suppression', 'Improved - on suppression'), ('Improved - further treatment planned', 'Improved - further treatment planned'), ('Failed', 'Failed')], max_length=200, null=True)),
                ('outcome_two_years_date', models.DateField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_rnoh_opatoutcomes_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('episode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Episode', verbose_name='Episode')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_rnoh_opatoutcomes_subrecords', to=settings.AUTH_USER_MODEL, verbose_name='Updated By')),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
    ]

# Generated by Django 2.0.13 on 2020-04-29 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('covid', '0005_covidpatient'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='covidreportingday',
            name='deaths',
        ),
        migrations.RemoveField(
            model_name='covidreportingday',
            name='tests_conducted',
        ),
        migrations.RemoveField(
            model_name='covidreportingday',
            name='tests_positive',
        ),
        migrations.AddField(
            model_name='covidreportingday',
            name='death',
            field=models.IntegerField(default=0, help_text='Number of patients who died on this day having tested positive for COVID 19'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='covidreportingday',
            name='lab_confirmed',
            field=models.IntegerField(default=0, help_text='Number of patients who first had a COVID 19 test positve result on this day'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='covidreportingday',
            name='tests_ordered',
            field=models.IntegerField(default=0, help_text='Number of COVID 19 tests ordered on this day'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='covidreportingday',
            name='tests_resulted',
            field=models.IntegerField(default=0, help_text='Number of COVID 19 tests reported on this day'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='covidreportingday',
            name='date',
            field=models.DateField(help_text='Date this data relates to'),
        ),
    ]

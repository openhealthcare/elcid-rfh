# Generated by Django 2.0.13 on 2021-01-05 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('covid', '0051_auto_20210105_1445'),
    ]

    operations = [
        migrations.AlterField(
            model_name='covidfollowupcall',
            name='breathlessness_trend',
            field=models.CharField(blank=True, choices=[('Same', 'Same'), ('Better', 'Better'), ('Worse', 'Worse'), ('Back to baseline', 'Back to baseline')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='covidfollowupcall',
            name='cough_trend',
            field=models.CharField(blank=True, choices=[('Same', 'Same'), ('Better', 'Better'), ('Worse', 'Worse'), ('Back to baseline', 'Back to baseline')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='covidfollowupcall',
            name='current_et',
            field=models.CharField(blank=True, choices=[('Reduced', 'Reduced'), ('Back to baseline', 'Back to baseline'), ('Unlimited', 'Unlimited')], max_length=50, null=True, verbose_name='Current ET'),
        ),
        migrations.AlterField(
            model_name='covidfollowupcall',
            name='fatigue_trend',
            field=models.CharField(blank=True, choices=[('Same', 'Same'), ('Better', 'Better'), ('Worse', 'Worse'), ('Back to baseline', 'Back to baseline')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='covidfollowupcall',
            name='sleep_quality_trend',
            field=models.CharField(blank=True, choices=[('Same', 'Same'), ('Better', 'Better'), ('Worse', 'Worse'), ('Back to baseline', 'Back to baseline')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='covidsixmonthfollowup',
            name='breathlessness_trend',
            field=models.CharField(blank=True, choices=[('Same', 'Same'), ('Better', 'Better'), ('Worse', 'Worse'), ('Back to Baseline', 'Back to Baseline')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='covidsixmonthfollowup',
            name='cough_trend',
            field=models.CharField(blank=True, choices=[('Same', 'Same'), ('Better', 'Better'), ('Worse', 'Worse'), ('Back to Baseline', 'Back to Baseline')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='covidsixmonthfollowup',
            name='current_et',
            field=models.CharField(blank=True, choices=[('Reduced', 'Reduced'), ('Back to baseline', 'Back to baseline'), ('Unlimited', 'Unlimited')], max_length=50, null=True, verbose_name='Current ET'),
        ),
        migrations.AlterField(
            model_name='covidsixmonthfollowup',
            name='fatigue_trend',
            field=models.CharField(blank=True, choices=[('Same', 'Same'), ('Better', 'Better'), ('Worse', 'Worse'), ('Back to Baseline', 'Back to Baseline')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='covidsixmonthfollowup',
            name='sleep_quality_trend',
            field=models.CharField(blank=True, choices=[('Same', 'Same'), ('Better', 'Better'), ('Worse', 'Worse'), ('Back to Baseline', 'Back to Baseline')], max_length=10, null=True),
        ),
    ]
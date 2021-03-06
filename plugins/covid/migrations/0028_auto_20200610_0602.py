# Generated by Django 2.0.13 on 2020-06-10 06:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('covid', '0027_auto_20200610_0536'),
    ]

    operations = [
        migrations.AddField(
            model_name='covidfollowupcall',
            name='tsq1',
            field=models.NullBooleanField(verbose_name='Upsetting thoughts or memories about your hospital admission that have come into your mind against your will'),
        ),
        migrations.AddField(
            model_name='covidfollowupcall',
            name='tsq10',
            field=models.NullBooleanField(verbose_name='Being jumpy or startled at something unexpected'),
        ),
        migrations.AddField(
            model_name='covidfollowupcall',
            name='tsq2',
            field=models.NullBooleanField(verbose_name='Upsetting dreams about the event'),
        ),
        migrations.AddField(
            model_name='covidfollowupcall',
            name='tsq3',
            field=models.NullBooleanField(verbose_name='Acting or feeling as though it is happening again'),
        ),
        migrations.AddField(
            model_name='covidfollowupcall',
            name='tsq4',
            field=models.NullBooleanField(verbose_name='Feeling upset by reminders of the event'),
        ),
        migrations.AddField(
            model_name='covidfollowupcall',
            name='tsq5',
            field=models.NullBooleanField(verbose_name='Bodily reactions such as fast heartbeat, sweatiness, dizziness when reminded of the event'),
        ),
        migrations.AddField(
            model_name='covidfollowupcall',
            name='tsq6',
            field=models.NullBooleanField(verbose_name='Difficulty falling or staying asleep'),
        ),
        migrations.AddField(
            model_name='covidfollowupcall',
            name='tsq7',
            field=models.NullBooleanField(verbose_name='Irritability or bursts of anger'),
        ),
        migrations.AddField(
            model_name='covidfollowupcall',
            name='tsq8',
            field=models.NullBooleanField(verbose_name='Difficulty concentrating'),
        ),
        migrations.AddField(
            model_name='covidfollowupcall',
            name='tsq9',
            field=models.NullBooleanField(verbose_name='Being more aware of potential danger to yourself and others'),
        ),
        migrations.AlterField(
            model_name='covidfollowupcall',
            name='depressed',
            field=models.CharField(blank=True, choices=[('0', 'Not At All'), ('1', 'Several days'), ('2', 'More than half the days'), ('3', 'Nearly every day')], max_length=50, null=True, verbose_name='Feeling down, depressed or hopeless'),
        ),
        migrations.AlterField(
            model_name='covidfollowupcall',
            name='interest',
            field=models.CharField(blank=True, choices=[('0', 'Not At All'), ('1', 'Several days'), ('2', 'More than half the days'), ('3', 'Nearly every day')], max_length=50, null=True, verbose_name='Little interest or pleasure in doing things'),
        ),
    ]

# Generated by Django 2.0.13 on 2021-02-05 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('covid', '0056_covidvaccination'),
    ]

    operations = [
        migrations.AlterField(
            model_name='covidfollowupcall',
            name='depressed',
            field=models.CharField(blank=True, choices=[('(0) Not At All', '(0) Not At All'), ('(1) Several days', '(1) Several days'), ('(2) More than half the days', '(2) More than half the days'), ('(3) Nearly every day', '(3) Nearly every day')], max_length=50, null=True, verbose_name='Feeling down, depressed or hopeless'),
        ),
        migrations.AlterField(
            model_name='covidfollowupcall',
            name='interest',
            field=models.CharField(blank=True, choices=[('(0) Not At All', '(0) Not At All'), ('(1) Several days', '(1) Several days'), ('(2) More than half the days', '(2) More than half the days'), ('(3) Nearly every day', '(3) Nearly every day')], max_length=50, null=True, verbose_name='Little interest or pleasure in doing things'),
        ),
        migrations.AlterField(
            model_name='covidsixmonthfollowup',
            name='depressed',
            field=models.CharField(blank=True, choices=[('(0) Not At All', '(0) Not At All'), ('(1) Several days', '(1) Several days'), ('(2) More than half the days', '(2) More than half the days'), ('(3) Nearly every day', '(3) Nearly every day')], max_length=50, null=True, verbose_name='Feeling down, depressed or hopeless'),
        ),
        migrations.AlterField(
            model_name='covidsixmonthfollowup',
            name='interest',
            field=models.CharField(blank=True, choices=[('(0) Not At All', '(0) Not At All'), ('(1) Several days', '(1) Several days'), ('(2) More than half the days', '(2) More than half the days'), ('(3) Nearly every day', '(3) Nearly every day')], max_length=50, null=True, verbose_name='Little interest or pleasure in doing things'),
        ),
    ]
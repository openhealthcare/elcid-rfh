# Generated by Django 2.0.13 on 2020-10-21 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('covid', '0048_covidsixmonthfollowup'),
    ]

    operations = [
        migrations.AddField(
            model_name='covidsixmonthfollowup',
            name='app_useful',
            field=models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No'), ('N/A', 'N/A')], max_length=250, null=True, verbose_name='Did you find the COVID recovery application useful?'),
        ),
        migrations.AddField(
            model_name='covidsixmonthfollowup',
            name='online_useful',
            field=models.CharField(blank=True, choices=[('Yes', 'Yes'), ('No', 'No'), ('N/A', 'N/A')], max_length=250, null=True, verbose_name='Did you find the online covid resource information useful?'),
        ),
        migrations.AlterField(
            model_name='covidsixmonthfollowup',
            name='cxrs',
            field=models.CharField(blank=True, choices=[('One', 'One'), ('Two or more', 'Two or more')], max_length=250, null=True, verbose_name='How many post discharge CXRs did the patient require?'),
        ),
    ]

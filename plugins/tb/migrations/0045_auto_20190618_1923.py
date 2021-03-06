# Generated by Django 2.0.13 on 2019-06-18 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tb', '0044_auto_20190617_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indexcase',
            name='relationship',
            field=models.CharField(blank=True, choices=[('Household', 'Household'), ('Healthcare', 'Healthcare'), ('Workplace (non healthcare)', 'Workplace (non healthcare)'), ('Education', 'Education'), ('Prison', 'Prison')], max_length=200, null=True, verbose_name='Relationship to index case'),
        ),
    ]

# Generated by Django 2.2.16 on 2022-01-25 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('labtests', '0009_auto_20211015_1244'),
    ]

    operations = [
        migrations.AddField(
            model_name='labtest',
            name='department_int',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]

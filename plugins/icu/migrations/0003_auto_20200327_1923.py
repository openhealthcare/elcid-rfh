# Generated by Django 2.0.9 on 2020-03-27 19:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('icu', '0002_auto_20200327_1911'),
    ]

    operations = [
        migrations.AddField(
            model_name='icuhandover',
            name='consistency_token',
            field=models.CharField(default=789789, max_length=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='icuhandover',
            name='created',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='icuhandover',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_icu_icuhandover_subrecords', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='icuhandover',
            name='updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='icuhandover',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_icu_icuhandover_subrecords', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='icuhandover',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opal.Patient'),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import opal.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('opal', '0025_merge'),
        ('elcid', '0003_bloodcultureisolate_consistency_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='LabTest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('updated', models.DateTimeField(null=True, blank=True)),
                ('object_id', models.PositiveIntegerField()),
                ('details', jsonfield.fields.JSONField(null=True, blank=True)),
                ('result', models.CharField(max_length=256, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(opal.models.UpdatesFromDictMixin, opal.models.ToDictMixin, models.Model),
        ),
        migrations.RemoveField(
            model_name='bloodcultureisolate',
            name='FISH',
        ),
        migrations.CreateModel(
            name='Fish',
            fields=[
                ('labtest_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='elcid.LabTest')),
            ],
            options={
                'abstract': False,
            },
            bases=('elcid.labtest',),
        ),
        migrations.AddField(
            model_name='labtest',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='labtest',
            name='created_by',
            field=models.ForeignKey(related_name='created_elcid_labtest_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='labtest',
            name='resistant_antibiotics',
            field=models.ManyToManyField(related_name='test_resistant', to='opal.Antimicrobial'),
        ),
        migrations.AddField(
            model_name='labtest',
            name='sensitive_antibiotics',
            field=models.ManyToManyField(related_name='test_sensitive', to='opal.Antimicrobial'),
        ),
        migrations.AddField(
            model_name='labtest',
            name='updated_by',
            field=models.ForeignKey(related_name='updated_elcid_labtest_subrecords', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]

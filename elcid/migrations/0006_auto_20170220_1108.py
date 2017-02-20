# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from elcid.patient_lists import Bacteraemia


def migrate_forwards(apps, schema_editor):
    PositiveBloodCultureHistory = apps.get_model(
        'elcid', 'PositiveBloodCultureHistory'
    )
    Episode = apps.get_model("opal", "Episode")
    episodes = Episode.objects.filter(tagging__value=Bacteraemia.tag)
    episodes = episodes.filter(patient__positivebloodculturehistory=None)
    for episode in episodes:
        tag = episode.tagging_set.filter(value=Bacteraemia.tag).first()
        PositiveBloodCultureHistory.objects.create(
            patient=episode.patient,
            when=tag.created
        )


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0005_auto_20170208_2135'),
    ]

    operations = [
        migrations.RunPython(
            migrate_forwards
        )
    ]

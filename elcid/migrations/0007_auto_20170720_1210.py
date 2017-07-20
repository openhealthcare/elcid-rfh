# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import reversion


def migrate_forwards(apps, schema_editor):
    Episode = apps.get_model("opal", "Episode")
    for e in Episode.objects.filter(start=None):
        location = e.location_set.first()
        reversions = reversion.get_for_object(location)

        if reversions:
            r = reversions[0]
            first_updated = r.field_dict["updated"]
            if first_updated:
                e.start = r.field_dict["updated"].date()
                e.save()


def migrate_backwards(app, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0006_auto_20170220_1108'),
        ('opal', '0031_auto_20170719_1018'),
    ]

    operations = [
        migrations.RunPython(
            migrate_forwards, reverse_code=migrate_backwards
        ),
    ]

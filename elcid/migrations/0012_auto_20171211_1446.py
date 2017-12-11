# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.contrib.contenttypes.models import ContentType
from opal.core.lookuplists import load_lookuplist_item

def lookup_drug_from_antimicrobial(apps, schema_editor):
    from opal.models import Synonym
    Antimicrobial = apps.get_model("opal", "Antimicrobial")
    Drug = apps.get_model("opal", "Drug")
    Allergy = apps.get_model("elcid", "Allergies")
    db_alias = schema_editor.connection.alias

    content_type = ContentType.objects.using(db_alias).get_for_model(Antimicrobial)
    for item in Antimicrobial.objects.using(db_alias).all():
        synonyms = [s.name for s in
                    Synonym.objects.using(db_alias).filter(content_type=content_type,
                                           object_id=item.id)]
        lookup = {'name': item.name, 'synonyms': synonyms}
        load_lookuplist_item(Drug, lookup)

    # for each allergy, set allergy.drug_temp to the value of allergy.drug
    for allergy in Allergy.objects.using(db_alias).all():

        allergy.drug_temp = allergy.drug


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0011_auto_20171211_1437'),
    ]

    operations = [
        migrations.RunPython(lookup_drug_from_antimicrobial)
    ]

# Generated by Django 2.0.13 on 2020-05-18 14:56

from django.db import migrations


def forwards(apps, schema_editor):
    """
    Create lookuplist entries for all Opal Microbiology_organism
    as Elcid MicrobiologyOrganisms
    """

    # Populate elcid MicrobiologyOrganism for all the
    # opal Microbiology_organisms
    Microbiology_organism = apps.get_model(
        'opal', 'Microbiology_organism'
    )
    MicrobiologyOrganism = apps.get_model(
        'elcid', 'MicrobiologyOrganism'
    )

    new_organisms = []
    for old_organism in Microbiology_organism.objects.all():
        new_organism = MicrobiologyOrganism(name=old_organism.name)
        new_organisms.append(new_organism)

    MicrobiologyOrganism.objects.bulk_create(new_organisms)


    # Create synonyms
    Synonym = apps.get_model(
        'opal', 'Synonym'
    )
    ContentType = apps.get_model(
        'contenttypes', "ContentType"
    )
    old_organism_ct = ContentType.objects.get_for_model(Microbiology_organism)
    new_organism_ct = ContentType.objects.get_for_model(MicrobiologyOrganism)

    synonyms = Synonym.objects.filter(content_type=old_organism_ct)

    for synonym in synonyms:
        organism_name = Microbiology_organism.objects.get(
            id=synonym.object_id
        ).name
        Synonym.objects.create(
            content_type=new_organism_ct,
            object_id=MicrobiologyOrganism.objects.get(name=organism_name).id,
            name=synonym.name
        )


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0047_auto_20200518_1452'),
    ]

    operations = [
        migrations.RunPython(
            forwards, backwards
        )
    ]

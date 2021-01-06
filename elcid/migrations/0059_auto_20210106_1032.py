from django.db import migrations


def forwards(apps, schema_editor):
    """
    Correct spellings
    """
    Antimicrobial = apps.get_model('elcid', 'Antimicrobial')

    for abx in Antimicrobial.objects.filter(treatment_reason="Targetted"):
        abx.treatment_reason = "Targeted"
        abx.save()

def backwards(apps, schema_editor):
    """
    Break spellings
    """
    Antimicrobial = apps.get_model('elcid', 'Antimicrobial')

    for abx in Antimicrobial.objects.filter(treatment_reason="Targeted"):
        abx.treatment_reason = "Targetted"
        abx.save()


class Migration(migrations.Migration):

    dependencies = [
        ('elcid', '0058_auto_20210106_1031'),
    ]

    operations = [
        migrations.RunPython(
            forwards, backwards
        )
    ]

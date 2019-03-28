from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db import transaction
from opal.models import Patient
from elcid import models


def get_key(lab_test):
    keys = ["aerobic", "lab_number", "source", "isolate"]
    extras = lab_test.extras
    return tuple([extras.get(i) for i in keys])


def save_blood_culture_isolate(patient, lab_tests):
    blood_culture_isolate = models.BloodCultureIsolate(patient=patient)
    # we have to save for the many to many fields
    blood_culture_isolate.save()

    lab_test_type_to_field = {
        models.BloodCultureOrganism.get_display_name(): "organism",
        models.GramStain.get_display_name(): "gram_stains",
        models.QuickFISH.get_display_name(): "quick_fish",
        models.GPCStaph.get_display_name(): "gpc_staph",
        models.GPCStrep.get_display_name(): "gpd_strep",
        models.GNR.get_display_name(): "gnr"
    }

    for lab_test in lab_tests:
        field = lab_test_type_to_field[lab_test.lab_test_type]
        if field == "gram_stains" and lab_test.result.result:
            gs = models.GramStainOutcome.objects.get(
                name=lab_test.result.result
            )
            blood_culture_isolate.gram_stains.add(gs)
        else:
            setattr(blood_culture_isolate, field, lab_test.result.result)

        blood_culture_isolate.lab_number = lab_test.extras.get("lab_number")
        blood_culture_isolate.aerobic = lab_test.extras.get("aerobic")
        blood_culture_isolate.source = lab_test.extras.get("source")
        blood_culture_isolate.created = lab_test.created
        blood_culture_isolate.created_by = lab_test.created_by
        blood_culture_isolate.updated = lab_test.updated
        blood_culture_isolate.updated_by = lab_test.updated_by
        dt = lab_test.datetime_ordered
        if dt:
            blood_culture_isolate.date_ordered = dt.date()

        blood_culture_isolate.sensitivities.add(
            *lab_test.sensitive_antibiotics.all()
        )
        blood_culture_isolate.resistances.add(
            *lab_test.resistant_antibiotics.all()
        )

    # saves the non many to many fields
    blood_culture_isolate.save()


@transaction.atomic
def sync_blood_cultures(patient):
    lab_tests = patient.labtest_set.exclude(lab_test_type__istartswith="up")
    by_key = defaultdict(list)
    for lab_test in lab_tests:
        by_key[get_key(lab_test)].append(lab_test)

    for lab_tests in by_key.values():
        save_blood_culture_isolate(patient, lab_tests)


class Command(BaseCommand):
    def handle(self, *args, **options):
        for patient in Patient.objects.all():
            if not patient.bloodcultureisolate_set.exists():
                sync_blood_cultures(patient)




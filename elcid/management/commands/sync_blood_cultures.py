from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db import transaction
from opal.models import Patient
from elcid import models


def get_key(lab_test):
    extras = lab_test.extras
    return (
        extras["lab_number"],
        extras["isolate"],
        extras.get("aerobic"),
        lab_test.datetime_ordered,
    )


def get_or_create_blood_culture_set(patient, old_lab_test):
    extras = old_lab_test.extras
    bcs_attrs = {"lab_number": extras.get("lab_number")}
    bcs_datetime_ordered = old_lab_test.datetime_ordered
    if bcs_datetime_ordered:
        bcs_attrs["date_ordered"] = bcs_datetime_ordered.date()
    source = extras.get("source")
    if source:
        source_model = models.BloodCultureSource.objects.filter(
            name=source
        ).first()
        if source_model:
            bcs_attrs["source_fk_id"] = source_model.id
        else:
            bcs_attrs["source_ft"] = source

    bcs, created = patient.bloodcultureset_set.get_or_create(
        **bcs_attrs
    )

    bcs.created = bcs.created or old_lab_test.created
    bcs.created_by = bcs.created_by or old_lab_test.created_by
    bcs.updated = bcs.updated or old_lab_test.updated
    bcs.updated_by = bcs.updated_by or old_lab_test.updated_by
    return bcs, created


def save_blood_culture_isolates(patient, old_lab_tests):
    bcs, _ = get_or_create_blood_culture_set(patient, old_lab_tests[0])

    old_field_to_new_field = {
        models.BloodCultureOrganism.get_display_name(): "organism",
        models.GramStain.get_display_name(): "gram_stain",
        models.QuickFISH.get_display_name(): "quick_fish",
        models.GPCStaph.get_display_name(): "gpc_staph",
        models.GPCStrep.get_display_name(): "gpc_strep",
        models.GNR.get_display_name(): "gnr"
    }

    isolate = models.BloodCultureIsolate(
        blood_culture_set=bcs
    )

    for old_lab_test in old_lab_tests:
        field = old_field_to_new_field[old_lab_test.lab_test_type]
        if old_lab_test.extras.get("aerobic") is True:
            isolate.aerobic_or_anaerobic = isolate.AEROBIC
        elif old_lab_test.extras.get("aerobic") is False:
            isolate.aerobic_or_anaerobic = isolate.ANAEROBIC
        setattr(isolate, field, old_lab_test.result.result)
        isolate.created = isolate.created or old_lab_test.created
        isolate.created_by = isolate.created_by or old_lab_test.created_by
        isolate.updated = isolate.updated or old_lab_test.updated
        isolate.updated_by = isolate.updated_by or old_lab_test.updated_by
        isolate.save()
        # We need to have saved the isolate before we can use M2M fields
        isolate.sensitivities.add(
            *old_lab_test.sensitive_antibiotics.all()
        )
        isolate.resistance.add(
            *old_lab_test.resistant_antibiotics.all()
        )
        isolate.save()


@transaction.atomic
def sync_blood_cultures(patient):
    lab_tests = patient.labtest_set.exclude(lab_test_type__istartswith="up")
    by_isolates = defaultdict(list)
    for lab_test in lab_tests:
        by_isolates[get_key(lab_test)].append(lab_test)

    for by_isolate in by_isolates.values():
        save_blood_culture_isolates(patient, by_isolate)


class Command(BaseCommand):
    def handle(self, *args, **options):
        for patient in Patient.objects.all():
            if not patient.bloodcultureset_set.exists():
                sync_blood_cultures(patient)


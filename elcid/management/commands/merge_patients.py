from django.core.management.base import BaseCommand
from django.db.models import Count
from opal.core import subrecords
from opal.models import Patient
from elcid.models import Demographics
import logging


logger = logging.getLogger('intrahospital_api')



subrecordsToIgnore = set([
    'InitialPatientLoad',
    'Demographics',
    'ContactInformation',
    'NextOfKinDetails',
    'GPDetails',
    'PositiveBloodCultureHistory',
    'ICUHandover',
    'ExternalDemographics',
])

def find_duplicates():
    """
    Returns the patients that are duplicates as a list of tuples
    where the tuples looks like (from_patient, to_patient,)
    ie the defunct patient and the patient to copy records to.
    """
    duplicate_patients = []
    unmergable = []
    dup_dempgraphics = (
        Demographics.objects.values("hospital_number")
        .annotate(cnt=Count("id"))
        .filter(cnt__gt=1)
    )
    duplicate_hns = [i["hospital_number"] for i in dup_dempgraphics if i["hospital_number"].strip()]
    logger.info(f'Found {len(duplicate_hns)} duplicate hns with the same number')
    for duplicate_hn in duplicate_hns:
        patients = Patient.objects.filter(
            demographics__hospital_number=duplicate_hn
        )
        if len(patients) > 2:
            # In theory this is not wrong, in practice it does not happen, so if it does
            # something unexpected has happened.
            raise ValueError(f'We have found {len(patients)} for hn {duplicate_hn}')
        patient_1 = patients[0]
        patient_1_native_records = elcid_native_records(patient_1)
        patient_2 = patients[1]
        patient_2_native_records = elcid_native_records(patient_2)
        if len(patient_1_native_records) and len(patient_2_native_records):
            logger.info(f'====== Unable to merge hn {duplicate_hn} as they both have duplicate records')
            logger.info(f'=== Patient 1 ({patient_1.id}) has:')
            for record in patient_1_native_records:
                logger.info(f'{record.__class__.__name__} {record.id}')
            logger.info(f'=== Patient 2 ({patient_2.id}) has:')
            for record in patient_2_native_records:
                logger.info(f'{record.__class__.__name__} {record.id}')
            unmergable.append((patient_1, patient_2,))
        elif len(patient_1_native_records) and not len(patient_2_native_records):
            duplicate_patients.append((patient_2, patient_1))
        else:
            duplicate_patients.append((patient_1, patient_2))
    return duplicate_patients, unmergable


def elcid_native_records(patient):
    result = []
    for subrecord in subrecords.episode_subrecords():
        if subrecord._is_singleton:
            result.extend(subrecord.objects.filter(episode__patient_id=patient.id).exclude(updated=None))
        else:
            result.extend(subrecord.objects.filter(episode__patient_id=patient.id))
    for subrecord in subrecords.patient_subrecords():
        if subrecord.__name__ in subrecordsToIgnore:
            continue
        if subrecord._is_singleton:
            result.extend(subrecord.objects.filter(patient_id=patient.id).exclude(updated=None))
        else:
            result.extend(subrecord.objects.filter(patient_id=patient.id))
    return result


class Command(BaseCommand):
    def handle(self, *args, **options):
        find_duplicates()

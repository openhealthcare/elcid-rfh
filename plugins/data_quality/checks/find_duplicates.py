import logging
from django.db.models import Count
from opal.core import subrecords
from opal.models import Patient
from elcid.models import Demographics
from plugins.data_quality import logger, utils


SUBRECORDS_TO_IGNORE = set([
    'InitialPatientLoad',
    'Demographics',
    'ContactInformation',
    'NextOfKinDetails',
    'GPDetails',
    'ExternalDemographics',
])



def find_exact_duplicates():
    """
    Returns
    Returns the patients that are duplicates as a list of tuples
    where the tuples looks like (from_patient, to_patient,)
    ie the defunct patient and the patient to copy records to.
    """
    dup_dempgraphics = (
        Demographics.objects.values("hospital_number")
        .annotate(cnt=Count("id"))
        .filter(cnt__gt=1)
    )
    duplicate_hns = [i["hospital_number"] for i in dup_dempgraphics if i["hospital_number"].strip()]
    if not duplicate_hns:
        # No patients with duplicate hospital numbers our work here is done.
        return
    dup_patients = []
    for duplicate_hn in duplicate_hns:
        patients = tuple(Patient.objects.filter(
            demographics__hospital_number=duplicate_hn
        ))
        if len(patients) > 2:
            # In theory this is not wrong, in practice it does not happen, so if it does
            # something unexpected has happened.
            raise ValueError(f'We have found {len(patients)} for hn {duplicate_hn}')
        dup_patients.append(patients)
    cleanable_duplicates, uncleanable_duplicates = calculate_deletable_undeletable(dup_patients)
    email_title = f'{len(cleanable_duplicates) + len (uncleanable_duplicates)} Exact hospital number duplicates'
    email_context = {
        "title": email_title,
        "cleanable_duplicates": cleanable_duplicates,
        "uncleanable_duplicates": uncleanable_duplicates
    }
    utils.send_email(
        email_title,
        "emails/duplicate_patients.html",
        email_context
    )


def find_zero_leading_duplicates():
    with_zero_hns = Demographics.objects.filter(
        hospital_number__startswith='0').values_list('hospital_number', flat=True
    )
    dup_patients = []
    for with_zero in with_zero_hns:
        without_zero = with_zero.lstrip('0')
        # We have patient numbers like 000. Don't match
        # these to an empty string
        if len(without_zero) == 0:
            continue
        with_zero_patients = list(Patient.objects.filter(
            demographics__hospital_number=with_zero
        ))
        without_zero_patients = list(Patient.objects.filter(
            demographics__hospital_number=without_zero
        ))
        if len(with_zero_patients) > 1 or len(without_zero_patients) > 1:
            # we expect these patients to be covered by the find_exact_duplicates
            # check
            continue
        if len(without_zero_patients) == 0:
            # we have no patients with the zero stripped so lets continue
            continue
        dup_patients.append((with_zero_patients[0], without_zero_patients[0],))
    if len(dup_patients) == 0:
        # if there are no duplicate patients, return
        return
    cleanable_duplicates, uncleanable_duplicates = calculate_deletable_undeletable(dup_patients)
    email_title = f'{len(cleanable_duplicates) + len (uncleanable_duplicates)} Exact hospital number duplicates'
    email_context = {
        "title": email_title,
        "cleanable_duplicates": cleanable_duplicates,
        "uncleanable_duplicates": uncleanable_duplicates
    }
    utils.send_email(
        email_title,
        "emails/duplicate_patients.html",
        email_context
    )


def has_records(patient):
    """
    Returns a list of populated the subrecords connected to the patient
    excluding the ones in SUBRECORD_TO_IGNORE
    """
    result = []
    for subrecord in subrecords.episode_subrecords():
        if subrecord._is_singleton:
            result.extend(subrecord.objects.filter(episode__patient_id=patient.id).exclude(updated=None))
        else:
            result.extend(subrecord.objects.filter(episode__patient_id=patient.id))
    for subrecord in subrecords.patient_subrecords():
        if subrecord.__name__ in SUBRECORDS_TO_IGNORE:
            continue
        if subrecord._is_singleton:
            result.extend(subrecord.objects.filter(patient_id=patient.id).exclude(updated=None))
        else:
            result.extend(subrecord.objects.filter(patient_id=patient.id))
    return result


def calculate_deletable_undeletable(patient_tuples):
    """
    Takes a list of tuples of patients that we think are the same.

    Sorts them into ones we can deal with and ones we can't.

    The first item in the tuple returned is a list of patient tuples where
    we can safely delete the first one.

    The second item in the tuple returned is a list of patient tuples
    where we do not know if we can delete them or not.

    ie
    returns a tuple of (
        [(to_delete, to_keep)],
        [(unmergable patient 1, unmergable patient 2)]
    )
    """
    unmergable = []
    duplicate_patients = []
    for patients in patient_tuples:
        patient_1 = patients[0]
        patient_1_native_records = has_records(patient_1)
        patient_1_hn = patient_1.demographics_set.get().hospital_number
        patient_2 = patients[1]
        patient_2_native_records = has_records(patient_2)
        patient_2_hn = patient_2.demographics_set.get().hospital_number
        if len(patient_1_native_records) and len(patient_2_native_records):
            logger.info(f'====== Unable to merge hn {patient_1_hn}/{patient_2_hn} as they both have duplicate records')
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

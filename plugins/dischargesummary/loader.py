"""
Load discharge summary data from upstream and save it
"""
import datetime

from django.db import transaction
from django.db.models import DateTimeField
from django.utils import timezone

from intrahospital_api.apis.prod_api import ProdApi as ProdAPI

from plugins.dischargesummary import logger
from plugins.dischargesummary.models import (
    DischargeSummary, DischargeMedication, PatientDischargeSummaryStatus
    )

Q_GET_SUMMARIES = """
SELECT *
FROM VIEW_ElCid_Freenet_TTA_Main
WHERE
RF1_NUMBER = @mrn
"""

Q_GET_MEDS_FOR_SUMMARY = """
SELECT *
FROM VIEW_ElCid_Freenet_TTA_Drugs
WHERE
TTA_Main_ID = @tta_id
"""


def save_summary_meds(summary, data):
    """
    Given a DischargeSummary and the raw data for the meds attached to it,
    save those meds.
    """
    our_meds = []
    for med in data:
        our_med = DischargeMedication(discharge=summary)
        for k, v in med.items():
            setattr(our_med, DischargeMedication.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k], v)
        our_meds.append(our_med)
    summary.medications.bulk_create(our_meds)


def load_dischargesummaries(patient):
    """
    Given a PATIENT load upstream discharge summary data and save it.
    """
    api = ProdAPI()

    summary_count = patient.dischargesummaries.count()

    mrn = patient.demographics().hospital_number
    other_mrns = list(
        patient.mergedmrn_set.values_list('mrn', flat=True)
    )
    mrns = [mrn] + other_mrns
    summaries = []
    for mrn in mrns:
        summaries.extend(api.execute_hospital_query(
            Q_GET_SUMMARIES,
            params={'mrn': mrn}
        ))

    for summary in summaries:

        meds = api.execute_hospital_query(
            Q_GET_MEDS_FOR_SUMMARY,
            params={'tta_id': summary['SQL_Internal_ID']}
        )

        parsed = {}
        for k, v in summary.items():
            if v: # Ignore empty values

                fieldtype = type(
                    DischargeSummary._meta.get_field(
                        DischargeSummary.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k]
                    )
                )
                if fieldtype == DateTimeField:
                    try:
                        v = timezone.make_aware(v)
                    except AttributeError:
                        # Only some of the "DateTime" fields are typed as such
                        v = datetime.datetime.strptime(v, '%d/%m/%Y %H:%M:%S')
                        v = timezone.make_aware(v)

                parsed[DischargeSummary.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k]] = v


        our_summary, _ = DischargeSummary.objects.get_or_create(
            patient=patient,
            date_of_admission=parsed['date_of_admission'],
            date_of_discharge=parsed['date_of_discharge']
        )

        for k, v in parsed.items():
            setattr(our_summary, k, v)

        with transaction.atomic():
            our_summary.save()
            our_summary.medications.all().delete()
            save_summary_meds(our_summary, meds)

        logger.info('Saved DischargeSummary {}'.format(our_summary.pk))

    if summary_count == 0:
        if len(summaries) > 0:
            # This is the first summary for this patient.
            status = PatientDischargeSummaryStatus.objects.get(patient=patient)
            status.has_dischargesummaries = True
            status.save()

    return

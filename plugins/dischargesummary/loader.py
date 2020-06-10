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
AND
LAST_UPDATED > @last_updated
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
    for med in data:
        our_med = DischargeMedication(discharge=summary)
        for k, v in med.items():
            setattr(our_med, DischargeMedication.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k], v)
        our_med.save()


def load_dischargesummaries(patient):
    """
    Given a PATIENT load upstream discharge summary data and save it.
    """
    api = ProdAPI()

    demographic = patient.demographics()

    summary_count = patient.dischargesummaries.count()

    if summary_count == 0:
        summary_date = datetime.datetime(1971, 1, 1, 1, 1, 1)
    else:
        summary_date = patient.dischargesummaries.all().order_by(
            'last_updated').last().date_updated

    summaries = api.execute_hospital_query(
        Q_GET_SUMMARIES,
        params={'mrn': demographic.hospital_number, 'last_updated': summary_date}
    )

    for summary in summaries:

        meds = api.execute_hospital_query(
            Q_GET_MEDS_FOR_SUMMARY,
            params={'tta_id': summary['SQL_Internal_ID']}
        )

        our_summary = DischargeSummary(patient=patient)

        for k, v in summary.items():
            if v: # Ignore empty values

                fieldtype = type(
                    DischargeSummary._meta.get_field(
                        DischargeSummary.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k]
                    )
                )
                if fieldtype == DateTimeField:
                    v = timezone.make_aware(v)

                setattr(
                    our_summary,
                    DischargeSummary.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
                    v
                )
        with transaction.atomic():
            our_summary.save()
            save_summary_meds(our_summary, data)

        logger.info('Saved DischargeSummary {}'.format(our_summary.pk))

    if summary_count == 0:
        if len(summaries) > 0:
            # This is the first summary for this patient.
            status = PatientDischargeSummaryStatus.objects.get(patient=patient)
            status.has_dischargesummaries = True
            status.save()

    return

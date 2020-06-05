"""
Load imaging data from upstream
"""
import datetime

from django.db.models import DateTimeField
from django.utils import timezone

from intrahospital_api.apis.prod_api import ProdApi as ProdAPI

from plugins.imaging.models import Imaging, PatientImagingStatus
from plugins.imaging import logger


Q_GET_IMAGING = """
SELECT *
FROM VIEW_ElCid_Radiology_Results
WHERE patient_number = @mrn
AND
date_reported > @reported_date
"""


def load_imaging(patient):
    """
    Given a PATIENT, load any upstream imaging reports we do not have
    """
    api = ProdAPI()

    demographic = patient.demographics()

    imaging_count = patient.imaging.count()

    if imaging_count > 0:
        reported_date = patient.imaging.all().order_by('date_reported').last().date_reported
    else:
        reported_date = datetime.datetime(1971, 1, 1, 1, 1, 1)

    imaging = api.execute_hospital_query(
        Q_GET_IMAGING,
        params={'mrn': demographic.hospital_number, 'reported_date': reported_date}
    )

    for report in imaging:
        our_imaging = Imaging(patient=patient)

        for k, v in report.items():
            if v: # Ignore empty values

                fieldtype = type(
                    Imaging._meta.get_field(Imaging.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k])
                )
                if fieldtype == DateTimeField:
                    v = timezone.make_aware(v)

                setattr(
                    our_imaging, Imaging.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k], v
                )

        our_imaging.save()
        logger.info('Saved Imaging {}'.format(our_imaging.pk))

    if imaging_count == 0:
        if len(imaging) > 0:
            # This is the first time we've seen imaging results for this patient
            # Toggle their imaging flag
            status = PatientImagingStatus.objects.get(patient=patient)
            status.has_imaging = True
            status.save()

"""
Load ICU Handover records from upstream
"""
import datetime

from django.db import transaction
from django.utils import timezone
from opal.models import Patient

from elcid.models import Demographics
from elcid.episode_categories import InfectionService
from elcid import utils
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api.loader import create_rfh_patient_from_hospital_number

from plugins.icu import logger
from plugins.icu.models import (
    ICUHandover, ICUHandoverLocation, parse_icu_location, ICUHandoverLocationHistory
)
from plugins.icu.episode_categories import ICUHandoverEpisode


Q_GET_ICU_HANDOVER = """
SELECT *
FROM VIEW_ElCid_ITU_Handover
WHERE discharged = 'No'
"""

Q_GET_ICU_MRNS = """
SELECT *
FROM VIEW_ElCid_ITU_Handover
WHERE discharged = 'No'
"""

def get_upstream_data():
    """
    Fetch the upstream handover snapshot data
    """
    api = ProdAPI()

    return api.execute_hospital_query(Q_GET_ICU_HANDOVER)


def get_upstream_mrns():
    """
    Return a list of MRNs of patients currently undischarged on
    the ICU Handover database
    """
    api = ProdAPI()

    return [p['Patient_MRN'] for p in api.execute_hospital_query(Q_GET_ICU_MRNS)]



def load_icu_handover():
    """
    Load a snapshot of data from the upstream appointment database
    """
    results = get_upstream_data()

    ICUHandoverLocation.objects.all().delete()

    upstream_mrns = [result['Patient_MRN'] for result in results]
    mrn_to_patients = utils.get_patients_from_mrns(upstream_mrns)

    for upstream_mrn in upstream_mrns:
        if upstream_mrn not in mrn_to_patients:
            # ICU handover MRNs can have preceding zeros, elCID does not use zero
            # prefixes as we match the upstream masterfile table
            mrn = upstream_mrn.lstrip('0')
            if mrn:
                patient = create_rfh_patient_from_hospital_number(
                    mrn, InfectionService
                )
                logger.info('Created patient for {}'.format(mrn))
                mrn_to_patients[upstream_mrn] = patient

    with transaction.atomic:
        for result in results:
            patient = mrn_to_patients.get(result['Patient_MRN'])

            if not patient:
                continue

            if not patient.episode_set.filter(
                    category_name=ICUHandoverEpisode.display_name).exists():
                patient.create_episode(category_name=ICUHandoverEpisode.display_name)

            our_handover, _ = ICUHandover.objects.get_or_create(patient=patient)

            for k, v in result.items():
                setattr(
                    our_handover,
                    ICUHandover.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k],
                    v
                )

            our_handover.save()

            handover_location, _ = ICUHandoverLocation.objects.get_or_create(
                patient=patient
            )
            hospital, ward, bed        = parse_icu_location(result['Location'])

            handover_location.hospital = hospital
            handover_location.ward     = ward
            handover_location.bed      = bed
            handover_location.admitted = result['Date_ITU_Admission'].date()
            handover_location.save()

            if ICUHandoverLocationHistory.objects.filter(patient=patient).exists():
                last = ICUHandoverLocationHistory.objects.filter(patient=patient).order_by('-timestamp')
                if last[0].location_string == result['Location']:
                    pass
                else:
                    ICUHandoverLocationHistory.objects.create(
                        patient=patient,
                        location_string=result['Location'],
                        timestamp=timezone.make_aware(datetime.datetime.now())
                    )


            else:
                ICUHandoverLocationHistory.objects.create(
                    patient=patient,
                    location_string=result['Location'],
                    timestamp=timezone.make_aware(datetime.datetime.now())
                )



            logger.info('Stored ICU Handover record for {}'.format(mrn))

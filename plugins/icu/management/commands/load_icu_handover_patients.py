"""
Management command to load ICU handover lists
"""
import traceback

from django.core.management.base import BaseCommand
from opal.models import Patient

from elcid.models import Demographics
from elcid.episode_categories import InfectionService
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api.loader import create_rfh_patient_from_hospital_number

from plugins.icu import logger
from plugins.icu.models import ICUHandover, ICUHandoverLocation, parse_icu_location
from plugins.icu.episode_categories import ICUHandoverEpisode

Q_GET_ICU_HANDOVER = """
SELECT * FROM VIEW_ElCid_ITU_Handover
"""

class Command(BaseCommand):
    def handle(self, *a, **k):
        try:
            api = ProdAPI()

            results = api.execute_hospital_query(Q_GET_ICU_HANDOVER)

            for result in results:

                mrn = result['Patient_MRN']

                if not Demographics.objects.filter(hospital_number=mrn).exists():
                    create_rfh_patient_from_hospital_number(mrn, InfectionService)

                    self.stdout.write(self.style.SUCCESS(
                        'Created patient for {}'.format(mrn)
                    ))

                patient = Patient.objects.get(demographics__hospital_number=mrn)

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
                handover_location.save()

                self.stdout.write(self.style.SUCCESS(
                    'Stored ICU Handover record for {}'.format(mrn)
                ))
        except:
            msg = 'Exception loading ICU Handover Patients \n {}'
            logger.error(msg.format(traceback.format_exc()))
        return

"""
Management command to pre-load Covid-19 patients
"""
from django.core.management.base import BaseCommand

from elcid.models import Demographics
from elcid.episode_categories import InfectionService
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api.loader import create_rfh_patient_from_hospital_number


Q_GET_COVID_IDS = """
SELECT DISTINCT Patient_Number FROM tQuest.Pathology_Result_view
WHERE OBR_exam_code_Text = '2019 NOVEL CORONAVIRUS'
"""

class Command(BaseCommand):
    def handle(self, *a, **k):
        api = ProdAPI()

        results = api.execute_trust_query(Q_GET_COVID_IDS)

        for result in results:

            mrn = result['Patient_Number']

            if Demographics.objects.filter(hospital_number=mrn).exists():
                continue

            create_rfh_patient_from_hospital_number(mrn, InfectionService)

            self.stdout.write(self.style.SUCCESS(
                'Created patient for {}'.format(hospital_number)
            ))


        return

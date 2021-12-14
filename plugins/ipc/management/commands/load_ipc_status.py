"""
A one of command to load the ipc status models that currently
exist upstream.

We do not expect this to happen multiple times so the logic
is just in this management command
"""
from collections import defaultdict
import datetime
import random
from django.db import transaction
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from opal.models import Patient
from elcid.models import Demographics
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from plugins.ipc import episode_categories
from plugins.ipc.models import IPCStatus


# We are not storing the fields below
# "Ver",
# "id",
# "insert_date",
# "nhs_number",
# "patient_dob",
# "patient_forename",
# "patient_surname",
# "Active",
# "Comment"
# "Handover_Last_Updated",
# "Last_Updated"


MAPPING = {
    "Acinetobacter": "acinetobacter",
    "Acinetobacter_LPS_Date": "acinetobacter_date",
    "CJD": "cjd",
    "CJD_LPS_Date": "cjd_date",
    "C_DIFFICILE": "c_difficile",
    "C_DIFFICILE_LPS_Date": "c_difficile_date",
    "Candida_auris": "candida_auris",
    "Candida_auris_date": "candida_auris_date",
    "Carb_resistance": "carb_resistance",
    "Carb_resistance_LPS_Date": "carb_resistance_date",
    "Contact_of_Acinetobacter": "contact_of_acinetobacter",
    "Contact_of_Acinetobacter_LPS_Date": "contact_of_acinetobacter_date",
    "Contact_of_Candida_auris": "contact_of_candida_auris",
    "Contact_of_Candida_auris_date": "contact_of_candida_auris_date",
    "Contact_of_Carb_resistance": "contact_of_carb_resistance",
    "Contact_of_Carb_resistance_LPS_Date": "contact_of_carb_resistance_lps_date",
    "Contact_of_Covid19": "contact_of_covid_19",
    "Contact_of_Covid19_Date": "contact_of_covid_19_date",
    "Covid19": "covid_19",
    "Covid19_Date": "covid_19_date",
    "MRSA": "mrsa",
    "MRSA_LPS_Date": "mrsa_date",
    "MRSA_neg": "mrsa_neg",
    "MRSA_neg_LPS_Date": "mrsa_neg_date",
    "Multi_drug_resistant_organism": "multi_drug_resistant_organism",
    "Multi_drug_resistant_organism_date": "multi_drug_resistant_organism_date",
    "Other": "other",
    "Other_Date": "other_date",
    "Other_Type": "other_type",
    "Patient_Number": "patient_number",
    "Reactive": "reactive",
    "Reactive_LPS_Date": "reactive_lps_date",
    "VRE": "vre",
    "VRE_LPS_Date": "vre_date",
    "VRE_Neg": "vre_neg",
    "VRE_Neg_LPS_Date": "vre_neg_date",
}

QUERY = """
SELECT * FROM ElCid_Infection_Prevention_Control_View
"""


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        api = ProdAPI()
        created = timezone.now()
        created_by = User.objects.filter(username='OHC').first()
        missing_nhs = 0
        missing_name = 0
        missing = 0
        IPCStatus.objects.all().delete()
        statuses = []
        upstream_result = api.execute_hospital_query(QUERY)
        nhs_num_to_patient = Demographics.objects.filter(
            nhs_number__in=[i["nhs_number"] for i in upstream_result]
        ).values_list('nhs_number', 'patient_id')
        nhs_num_to_patient_ids = defaultdict(list)
        for nhs_num, patient_id in nhs_num_to_patient:
            nhs_num_to_patient_ids[nhs_num].append(patient_id)

        for row in upstream_result:
            patients = []
            patient_ids = nhs_num_to_patient_ids.get(row["nhs_number"], [])
            if patient_ids:
                patients = Patient.objects.get(id__in=patient_ids)
            if not patients:
                missing_nhs += 1
                patients = Patient.objects.filter(
                    demographics__first_name=row["patient_forename"],
                    demographics__surname=row["patient_surname"],
                    demographics__date_of_birth=row["patient_dob"],
                )
                missing_name += 1
            if not patients:
                missing += 1

            for patient in patients:
                update_dict = {v: row[k] for k, v in MAPPING.items()}
                status = IPCStatus(
                    patient=patient,
                    created=created,
                    created_by=created_by
                )
                for key, value in update_dict.items():
                    if isinstance(value, datetime.datetime):
                        value = timezone.make_aware(value)
                    setattr(status, key, value)
                    statuses.append(status)
        IPCStatus.objects.bulk_create(statuses)
        ended = timezone.now()
        self.stdout.write(f"Statuses created in {ended - created}s")
        self.stdout.write(f"Missing nhs number {missing_nhs}")
        self.stdout.write(f"Missing name {missing_name}")
        self.stdout.write(f"Missing {missing}")
        self.stdout.write(f"Created {len(statuses)} statuses")
        examples = Patient.objects.filter(
            id__in=[i.patient_id for i in statuses]
        ).filter(
            episode__category_name=episode_categories.IPCEpisode.display_name
        )
        self.stdout.write('Example patients:')
        for _ in range(4):
            idx = random.randint(len(examples))
            self.stdout.write(
                examples[idx].demographics().name
            )

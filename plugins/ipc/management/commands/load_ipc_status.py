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
from django.db.models.fields import BooleanField, DateField
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
    "Comment": "comments",
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
    "Contact_of_Carb_resistance_LPS_Date": "contact_of_carb_resistance_date",
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
    "Other_Date": "other_date",
    "Other_Type": "other",
    "Reactive": "reactive",
    "Reactive_LPS_Date": "reactive_date",
    "VRE": "vre",
    "VRE_LPS_Date": "vre_date",
    "VRE_Neg": "vre_neg",
    "VRE_Neg_LPS_Date": "vre_neg_date",
}

QUERY = """
SELECT * FROM ElCid_Infection_Prevention_Control_View
"""


def construct_cache(upstream_result):
    mrn_to_patient_ids = defaultdict(set)
    mrn_and_patient = Demographics.objects.filter(
        hospital_number__in=[i["Patient_Number"] for i in upstream_result if i["Patient_Number"]]
    ).values_list('hospital_number', 'patient_id')
    for mrn, patient_id in mrn_and_patient:
        mrn_to_patient_ids[mrn].add(patient_id)
    return mrn_to_patient_ids


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        api = ProdAPI()
        created = timezone.now()
        created_by = User.objects.filter(username='OHC').first()
        missing = 0
        IPCStatus.objects.all().delete()
        statuses = []
        upstream_result = api.execute_hospital_query(QUERY)
        self.stdout.write("Query complete")

        mrn_to_patient_ids = construct_cache(upstream_result)
        self.stdout.write("Cache constructed")

        for row in upstream_result:
            patients = []
            mrn_to_patient_ids
            patient_ids = mrn_to_patient_ids.get(row["Patient_Number"], [])
            if not patient_ids:
                missing += 1
                continue
            patients = Patient.objects.filter(id__in=patient_ids)

            for patient in patients:
                update_dict = {k: row[k] for k in MAPPING.keys()}

                status = IPCStatus(
                    patient=patient,
                    created=created,
                    updated=created,
                    created_by=created_by,
                    updated_by=created_by
                )
                for key, value in update_dict.items():
                    if isinstance(IPCStatus._meta.get_field(MAPPING[key]), DateField):
                        if value == '':
                            value = None
                        elif isinstance(value, str):
                            value = datetime.datetime.strptime(value, '%d/%m/%Y').date()
                    if isinstance(IPCStatus._meta.get_field(MAPPING[key]), BooleanField):
                        if isinstance(value, str):
                            if value == '':
                                value = False
                            # we get rows like MRSA neg as string fields in the mrsa_neg column
                            elif key.lower() == value.lower() or key.lower().replace("_", " ") == value.lower():
                                value = True
                            elif key == 'Covid19' and value == 'Covid-19':
                                value = True
                    setattr(status, MAPPING[key], value)
                statuses.append(status)
        self.stdout.write("Statuses constructed")
        IPCStatus.objects.bulk_create(statuses, batch_size=1000)
        ended = timezone.now()
        self.stdout.write(f"Statuses created in {ended - created}s")
        self.stdout.write(f"Missing {missing}")
        self.stdout.write(f"Created {len(statuses)} statuses")
        examples = Patient.objects.filter(
            id__in=[i.patient_id for i in statuses]
        ).filter(
            episode__category_name=episode_categories.IPCEpisode.display_name
        )
        self.stdout.write('Example patients:')
        for _ in range(4):
            idx = random.randint(0, len(examples))
            self.stdout.write(
                examples[idx].demographics().name
            )

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

from plugins.admissions.models import BedStatus
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
    "Comment": "comments"
}


QUERY = """
SELECT * FROM ElCid_Infection_Prevention_Control_View
"""


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        api = ProdAPI()

        updated = timezone.now()
        updated_by = User.objects.filter(username='OHC').first()

        inpatients = BedStatus.objects.filter(bed_status='Occupied').values_list(
            'local_patient_identifier', flat=True)

        upstream_result = api.execute_hospital_query(QUERY)

        self.stdout.write("Query complete")

        for row in upstream_result:
            if row['Patient_Number'] in inpatients:
                patient = Patient.objects.get(demographics__hospital_number=row['Patient_Number'])

                if patient.episode_set.filter(category_name='IPC').count() == 0:
                    patient.create_episode(category_name='IPC')

                status = patient.ipcstatus_set.all()[0]

                update_dict = {v: row[k] for k, v in MAPPING.items()}

                status.created_by_id = updated_by.id

                for key, value in update_dict.items():

                    if isinstance(IPCStatus._meta.get_field(key), DateField):

                        if value == '':
                            value = None
                        elif isinstance(value, str):
                            value = datetime.datetime.strptime(value, '%d/%m/%Y').date()

                    if isinstance(IPCStatus._meta.get_field(key), BooleanField):
                        if value:
                            value = True
                        value = False

                    setattr(status, key, value)
                status.save()

from django.core.management.base import BaseCommand
from django.db import connection
import pytds
import csv
import os
from django.conf import settings
from plugins.appointments import models as appointment_models
from elcid import models as elcid_models
from django.db.models import DateTimeField
from django.utils import timezone
from elcid import utils
import datetime

CSV_NAME = "all_appointments.csv"

LOAD_ALL_APPOINTMENTS = """
SELECT * FROM VIEW_ElCid_CRS_OUTPATIENTS
"""


def call_db_command(sql):
    with connection.cursor() as cursor:
        cursor.execute(
            sql
        )


def get_mrn_to_patient_id():
    """
    Returns a map of all MRNs from demographics and Merged MRN
    to the corresponding patient id.
    """
    mrn_to_patient_id = {}
    demographics_mrn_and_patient_id = list(
        elcid_models.Demographics.objects.exclude(
            hospital_number=None,
        )
        .exclude(hospital_number="").filter(
            patient__appointments=None
        )
        .values_list("hospital_number", "patient_id")
    )

    for mrn, patient_id in demographics_mrn_and_patient_id:
        mrn_to_patient_id[mrn] = patient_id

    merged_mrn_and_patient_id = list(
        elcid_models.MergedMRN.objects.filter(
            patient__appointments=None
        ).values_list("mrn", "patient_id")
    )

    for mrn, patient_id in merged_mrn_and_patient_id:
        mrn_to_patient_id[mrn] = patient_id

    return mrn_to_patient_id


def cast_to_row(patient_id, upstream_dict):
    row = {"patient_id": patient_id}
    for k, v in upstream_dict.items():
        if v:  # Ignore empty values
            fieldtype = type(
                appointment_models.Appointment._meta.get_field(appointment_models.Appointment.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k])
            )
            if fieldtype == DateTimeField:
                v = timezone.make_aware(v)
        row[appointment_models.Appointment.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k]] = v
    return row


def create_csv():
    mrn_to_patient_id = get_mrn_to_patient_id()
    with open(CSV_NAME, "w") as csv_file:
        writer = None
        with pytds.connect(
            settings.HOSPITAL_DB["ip_address"],
            settings.HOSPITAL_DB["database"],
            settings.HOSPITAL_DB["username"],
            settings.HOSPITAL_DB["password"],
            as_dict=True,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(LOAD_ALL_APPOINTMENTS)
                while True:
                    rows = cur.fetchmany()
                    if not rows:
                        break
                    for upstream_row in rows:
                        mrn = upstream_row["vPatient_Number"]
                        if not mrn:
                            continue
                        if not mrn.lstrip('0').strip():
                            continue
                        patient_id = mrn_to_patient_id.get(mrn)
                        if not patient_id:
                            continue
                        row = cast_to_row(patient_id, upstream_row)
                        if writer is None:
                            writer = csv.DictWriter(csv_file, fieldnames=row.keys())
                            writer.writeheader()
                        writer.writerow(row)
    return


def get_csv_headers():
    headers = []
    with open(CSV_NAME) as r:
        reader = csv.DictReader(r)
        row = next(reader)
        headers = list(row.keys())
    return headers


class Command(BaseCommand):
    @utils.timing
    def handle(self, *args, **options):
        create_csv()
        columns = ",".join(get_csv_headers())
        pwd = os.getcwd()
        appointment_csv = os.path.join(pwd, CSV_NAME)
        cmd = f"COPY appointments_appointment ({columns}) FROM '{appointment_csv}' WITH (FORMAT csv, header);"
        call_db_command(cmd)
        admissions_models.PatientAppointmentStatus.objects.filter(patient__appointments__isnull=False).update(
            has_appointments=True
        )
        os.remove(appointment_csv)

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
import subprocess
from django.db import models
from elcid import models as elcid_models
from elcid.utils import timing
from plugins.admissions.models import TransferHistory
import datetime
import pytds
import csv
import os


FILE_NAME = "transfer_history.csv"


def to_datetime(v):
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"]
    if isinstance(v, datetime.datetime):
        return v
    for format in formats:
        try:
            dt = datetime.datetime.strptime(v, format)
            if dt:
                break
        except Exception:
            if format == formats[-1]:
                raise
    return timezone.make_aware(dt)


def get_column_headers():
    return list(
        TransferHistory.UPSTREAM_FIELDS_TO_MODEL_FIELDS.values()
    ) + ["patient_id", "created_in_elcid"]


@timing
def stream_result():
    query = """
    SELECT * FROM INP.TRANSFER_HISTORY_EL_CID WITH (NOLOCK)
    WHERE LOCAL_PATIENT_IDENTIFIER is not null
    and LOCAL_PATIENT_IDENTIFIER <> ''
    AND In_TransHist = 1
    AND In_Spells = 1
    ORDER BY LOCAL_PATIENT_IDENTIFIER, ENCNTR_SLICE_ID
    """
    mrn_and_patient_id = elcid_models.Demographics.objects.values_list(
        "hospital_number", "patient_id"
    )
    mrn_to_patient_id = {
        mrn: patient_id for mrn, patient_id in mrn_and_patient_id if mrn
    }
    with open(FILE_NAME, "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=get_column_headers())
        writer.writeheader()
        with pytds.connect(
            settings.WAREHOUSE_DB["ip_address"],
            settings.WAREHOUSE_DB["database"],
            settings.WAREHOUSE_DB["username"],
            settings.WAREHOUSE_DB["password"],
            as_dict=True,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                while True:
                    result = cur.fetchmany()
                    if result:
                        for upstream_row in result:
                            row_mrn = upstream_row["LOCAL_PATIENT_IDENTIFIER"]
                            if row_mrn not in mrn_to_patient_id:
                                continue
                            patient_id = mrn_to_patient_id[row_mrn]
                            row = {"patient_id": patient_id}
                            for k, v in upstream_row.items():
                                field = (
                                    TransferHistory.UPSTREAM_FIELDS_TO_MODEL_FIELDS.get(
                                        k
                                    )
                                )
                                if field:
                                    row[field] = v
                                    if isinstance(
                                        TransferHistory._meta.get_field(field),
                                        models.DateTimeField,
                                    ):
                                        row[field] = to_datetime(v)
                                row["patient_id"] = patient_id
                                row["created_in_elcid"] = timezone.now()
                            writer.writerow(row)
                    if not result:
                        break


def call_db_command(sql):
    """
    Calls a command on our database via psql
    """
    subprocess.call(f"psql --echo-all -d {settings.DATABASES['default']['NAME']} -c '{sql}'", shell=True)


def delete_existing_transfer_histories():
    """
    Delete all existing transfer histories
    """
    call_db_command("truncate table admissions_transferhistory")


def copy_transfer_histories():
    """
    Runs the psql copy command to copy transfer histories from
    FILE_NAME into our transfer history table
    """
    columns = ",".join(get_column_headers())
    pwd = os.getcwd()
    transfer_history_csv = os.path.join(pwd, FILE_NAME)
    cmd = f"\copy admissions_transferhistory ({columns}) FROM '{transfer_history_csv}' WITH (FORMAT csv, header);"
    call_db_command(cmd)


class Command(BaseCommand):
    def handle(self, *args, **options):
        stream_result()
        delete_existing_transfer_histories()
        copy_transfer_histories()

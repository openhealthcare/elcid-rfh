import csv
import pytds
import datetime
from django.conf import settings
from django.db.models import TextField, CharField
from django.core.management import BaseCommand
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from elcid.models import Demographics, ContactInformation, NextOfKinDetails, MasterFileMeta, GPDetails
from django.core.mail import send_mail
from opal.core.fields import ForeignKeyOrFreeText

FILE_NAME = "upstream_demographics.csv"


def send_report(report):
    dt = datetime.datetime.now().strftime("%d/%m/%Y")
    send_mail(
        f"Demographics report {dt}",
        report,
        settings.DEFAULT_FROM_EMAIL,
        ["fred.kingham@openhealthcare.org.uk"],
    )


DEMOGRAPHICS_INFORMATION_MAPPING = {
    "hospital_number": "PATIENT_NUMBER",
    "nhs_number": "NHS_NUMBER",
    "first_name": "FORENAME1",
    "middle_name": "FORENAME2",
    "surname": "SURNAME",
    "title": "TITLE",
    "religion": "RELIGION",
    "marital_status": "MARITAL_STATUS",
    "nationality": "NATIONALITY",
    "main_language": "MAIN_LANGUAGE",
    "date_of_birth": "DOB",
    "sex": "SEX",
    "ethnicity": "ETHNIC_GROUP",
    "date_of_death": "DATE_OF_DEATH",
    "death_indicator": "DEATH_FLAG",
}

CONTACT_INFORMATION_MAPPING = {
    "address_line_1": "ADDRESS_LINE1",
    "address_line_2": "ADDRESS_LINE2",
    "address_line_3": "ADDRESS_LINE3",
    "address_line_4": "ADDRESS_LINE4",
    "postcode": "POSTCODE",
    "home_telephone": "HOME_TELEPHONE",
    "work_telephone": "WORK_TELEPHONE",
    "mobile_telephone": "MOBILE_TELEPHONE",
    "email": "EMAIL",
}

NOK_MAPPING = {
    "nok_type": "NOK_TYPE",
    "surname": "NOK_SURNAME",
    "forename_1": "NOK_FORENAME1",
    "forename_2": "NOK_FORENAME2",
    "relationship": "NOK_relationship",
    "address_1": "NOK_address1",
    "address_2": "NOK_address2",
    "address_3": "NOK_address3",
    "address_4": "NOK_address4",
    "postcode": "NOK_Postcode",
    "home_telephone": "nok_home_telephone",
    "work_telephone": "nok_work_telephone",
}

GP_DETAILS = {
    "crs_gp_masterfile_id": "CRS_GP_MASTERFILE_ID",
    "national_code": "GP_NATIONAL_CODE",
    "practice_code": "GP_PRACTICE_CODE",
    "title": "gp_title",
    "initials": "GP_INITIALS",
    "surname": "GP_SURNAME",
    "address_1": "GP_ADDRESS1",
    "address_2": "GP_ADDRESS2",
    "address_3": "GP_ADDRESS3",
    "address_4": "GP_ADDRESS4",
    "postcode": "GP_POSTCODE",
    "telephone": "GP_TELEPHONE",
}

MASTERFILE_META = {
    "insert_date": "INSERT_DATE",
    "last_updated": "LAST_UPDATED",
    "merged": "MERGED",
    "merge_comments": "MERGE_COMMENTS",
    "active_inactive": "ACTIVE_INACTIVE",
}


MODEL_MAPPING = {
    Demographics: DEMOGRAPHICS_INFORMATION_MAPPING,
    ContactInformation: CONTACT_INFORMATION_MAPPING,
    NextOfKinDetails: NOK_MAPPING,
    GPDetails: GP_DETAILS,
    MasterFileMeta: MASTERFILE_META,
}


def check_field_is_populated(model, mapping, our_field):
    upstream_result = 0
    with open('upstream_demographics.csv') as upstream_file:
        reader = csv.DictReader(upstream_file)
        for row in reader:
            if not row[mapping[our_field]] == '':
                upstream_result += 1
    if isinstance(getattr(model, our_field), ForeignKeyOrFreeText):
        str_field_name = f"{our_field}_ft"
        related_field_name = f"{our_field}_fk_id"
        str_qs = model.objects.exclude(**{str_field_name: ""}).exclude(**{str_field_name: None}).count()
        related_qs = model.objects.exclude(**{related_field_name: None}).count()
        qs = str_qs + related_qs
    elif isinstance(model._meta.get_field(our_field), (TextField, CharField)):
        qs = (
            model.objects.exclude(**{our_field: ""})
            .exclude(**{our_field: None})
            .count()
        )
    else:
        qs = (
            model.objects.exclude(**{our_field: None})
            .count()
        )
    our_result = qs
    return our_result, upstream_result


def get_column_names():
    api = ProdAPI()
    query = """
    SELECT TOP(1) * FROM VIEW_CRS_Patient_Masterfile
    """
    result = api.execute_hospital_query(query)
    return list(result[0].keys())


def stream_result():
    query = """
    SELECT * FROM VIEW_CRS_Patient_Masterfile
    WHERE PATIENT_NUMBER <> ''
    AND PATIENT_NUMBER is not null
    ORDER BY PATIENT_NUMBER
    """
    our_hns = set(Demographics.objects.values_list("hospital_number", flat=True))
    with open(FILE_NAME, "w") as csv_file:
        headers = get_column_names()
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        with pytds.connect(
            settings.HOSPITAL_DB["ip_address"],
            settings.HOSPITAL_DB["database"],
            settings.HOSPITAL_DB["username"],
            settings.HOSPITAL_DB["password"],
            as_dict=True,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                while True:
                    result = cur.fetchmany()
                    if result:
                        for row in result:
                            if row["PATIENT_NUMBER"] in our_hns:
                                writer.writerow(row)
                    if not result:
                        break


def reconcile_field(model, field):
    field_mapping = MODEL_MAPPING[model]
    if isinstance(getattr(model, field), ForeignKeyOrFreeText):
        raise ValueError('this does not work for foreign key and free text')
    if model == Demographics:
        hn_lookup = 'hospital_number'
    else:
        hn_lookup = 'patient__demographics__hospital_number'
    qs = model.objects.exclude(patient__masterfilemeta=None)
    maps = qs.values_list(hn_lookup, field)
    mapping = {i: v for i, v in maps}
    incorrect = 0
    missing = 0
    with open(FILE_NAME) as csv_file:
        reader = csv.DictReader(csv_file)
        for i in reader:
            mrn = i["PATIENT_NUMBER"]
            if mrn not in mapping:
                missing += 1
                continue
            their_value = i[field_mapping[field]]
            if isinstance(their_value, str):
                their_value = their_value.lower()
            our_value = mapping[mrn]
            if field == "date_of_birth" and our_value:
                our_value = our_value.strftime('%Y-%m-%d') + " 00:00:00"
            if isinstance(our_value, str):
                our_value = our_value.lower()
            if isinstance(our_value, datetime.datetime):
                our_value = str(our_value)
            if our_value is None or our_value is '':
                if their_value is None or their_value is '':
                    continue
                else:
                    incorrect += 1
            elif not their_value == our_value:
                incorrect += 1
    return incorrect, missing

def format_results(incorrect_and_missing):
    incorrect = incorrect_and_missing[0]
    missing = incorrect_and_missing[1]
    return f"Incorrect: {incorrect}, Missing: {missing}\n\n"


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        started = datetime.datetime.now()
        stream_result()
        fields_to_check = (
            (Demographics, 'first_name',),
            (Demographics, 'surname',),
            (Demographics, 'date_of_birth',),
            (ContactInformation, 'address_line_1',),
            (ContactInformation, 'postcode',),
            (NextOfKinDetails, 'nok_type',),
            (NextOfKinDetails, 'surname',),
            (GPDetails, 'initials',),
            (GPDetails, 'surname',),
            (MasterFileMeta, 'insert_date',),
            (MasterFileMeta, 'last_updated',),
        )
        result = ""
        last_model = None
        for model, field in fields_to_check:
            if last_model is None:
                result += f"=== {model.__name__}\n"
            elif not last_model == model:
                result += f"\n=== {model.__name__}\n"
            last_model = model
            result += f"{field}\n"
            result += format_results(reconcile_field(model, field))
        ended = datetime.datetime.now()
        result += f"report started in {str(started)} and ended in {ended}"
        send_report(result)

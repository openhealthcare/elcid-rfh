"""
Write a summary of results back upstream as plain text for display
within other applications.
"""
import datetime

from django.conf import settings
from django.template.loader import get_template

from elcid.models import Demographics, MicrobiologyInput
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from plugins.covid.lab import get_covid_result_ticker
from plugins.icu.loader import get_upstream_mrns


ADVICE_INSERT = """
INSERT INTO ElCid_Reports (
  elcid_version,
  elcid_clinical_advice_id,
  elcid_patient_id,
  written_by,
  datetime_inserted,
  hospital_number,
  patient_forename,
  patient_surname,
  agreed_plan,
  infection_control,
  datetime_issued
)
VALUES
(
  @elcid_version,
  @elcid_clinical_advice_id,
  @elcid_patient_id,
  @written_by,
  @datetime_inserted,
  @hospital_number,
  @patient_forename,
  @patient_surname,
  @agreed_plan,
  @infection_control,
  @datetime_issued
)
"""

RESULTS_INSERT = """
INSERT INTO ElCid_Reports (
  elcid_version,
  elcid_patient_id,
  datetime_inserted,
  hospital_number,
  patient_forename,
  patient_surname,
  COVID19_result
)
VALUES
(
  @elcid_version,
  @elcid_patient_id,
  @datetime_inserted,
  @hospital_number,
  @patient_forename,
  @patient_surname,
  @covid_results
)
"""

def serialise_summary(patient):
    """
    Given a PATIENT return a string summarising their COVID results
    """
    ticker   = get_covid_result_ticker(patient)
    template = get_template('intrahospital_api/result_ticker.html')

    return template.render({'ticker': ticker})


def write_result_summary():
    """
    For all patients currently undischarged on the ICU Handover database,
    write a text summary of their COVID results to the upstream database
    """
    upstream_mrns = get_upstream_mrns()
    demographics  = Demographics.objects.filter(hospital_number__in=upstream_mrns)
    summaries = [
        (d, serialise_summary(d.patient)) for d in demographics
    ]

    api = ProdAPI()

    for demographic, summary_text in summaries:
        params = {
            'elcid_version'    : settings.VERSION_NUMBER,
            'elcid_patient_id' : demographic.patient_id,
            'datetime_inserted': datetime.datetime.now(),
            'hospital_number'  : demographic.hospital_number,
            'patient_forename' : demographic.first_name,
            'patient_surname'  : demographic.surname,
            'covid_results'    : summary_text
        }
        api.execute_hospital_insert(RESULTS_INSERT, params=params)

    return


def write_advice_upstream(advice_id):
    """
    Given the ID of a MicrobiologyInput entry, write it upstream.
    """
    advice = MicrobiologyInput.objects.get(id=advice_id)

    if not advice.agreed_plan and not advice.infection_control:
        return

    demographic = advice.episode.patient.demographics()

    params = {
        'elcid_version'           : settings.VERSION_NUMBER,
        'elcid_clinical_advice_id': advice.id,
        'elcid_patient_id'        : advice.episode.patient_id,
        'written_by'              : advice.initials,
        'datetime_inserted'       : datetime.datetime.now(),
        'hospital_number'         : demographic.hospital_number,
        'patient_forename'        : demographic.first_name,
        'patient_surname'         : demographic.surname,
        'agreed_plan'             : advice.agreed_plan,
        'infection_control'       : advice.infection_control,
        'datetime_issued'         : advice.when
    }

    api = ProdAPI()
    if settings.WRITEBACK_ON:
        api.execute_hospital_insert(ADVICE_INSERT, params=params)

"""
Load RNOH Database from upstream.

This is not a BAU process, but a one off import to enable the
decommissioning of the upstream service.

We store the historic RNOH database to maintain access to this clinical
documentation for the team.
"""
import datetime

from django.db import transaction
from opal.models import Patient

from elcid.models import Demographics
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI

from plugins.rnoh.models import PatientRNOHSBARStatus, RNOHSBAR, RNOHDemographics

Q_GET_ALL_HANDOVER = """
SELECT *
FROM HandoverDB.SHIFT_HANDOVERS_X
WHERE
ver = 330697
AND
specialty = 'RNOH'
"""

def get_RAN_MRN(mrn):
    """
    Strip the RAN Suffix if it exists
    """
    # The true RAN MRN
    try:
        int(mrn[-1])
    except ValueError:
        mrn = mrn[:-1]
    return mrn


def get_or_create_RNOH_patient(data):
    """
    Given DATA - as returned from the upstream database, return
    an elCID patient for that data.

    Match priority:
    - NHS Number
    - RAN MRN
    - name
        - Plus DOB

    Default to create duplicates first.

    If the patient does not exist, create it.
    """
    created = False

    mrn = data['rf1_number']

    if not mrn.startswith('RAN'):
        raise ValueError(f"{mrn} does not begin with RAN")

    mrn = get_RAN_MRN(mrn)


    if data['nhs_number']:
        try:
            demographics = Demographics.objects.get(nhs_number=data['nhs_number'])
            patient = demographics.patient

            # Ensure they have the appropriate RAN MRN
            rnoh_demographics = patient.rnohdemographics_set.get()

            rnoh_demographics.rnoh_hospital_number = mrn
            rnoh_demographics.save()

            return patient, created
        except Demographics.DoesNotExist:
            pass

    if mrn:

        try:
            demographics = RNOHDemographics.objects.get(rnoh_hospital_number=mrn)
            return demographics.patient, created
        except RNOHDemographics.DoesNotExist:
            pass

    first, last, dob = data['patient_forename'], data['patient_surname'], data['patient_dob']

    dob = datetime.datetime.strptime(dob, '%d/%m/%Y').date()

    # Only attempt a match if all three exist
    if first:
        if last:
            if dob:
                try:
                    demographics = Demographics.objects.get(surname=last, forename=first, dob=dob)
                    return demographics.patient, created
                except Demographics.DoesNotExist:
                    pass

    # We can't find them, create them.
    patient = Patient.objects.create()
    demographics = patient.demographics_set.get()

    demographics.forename = first
    demographics.surname  = last
    demographics.dob      = dob
    demographics.save()

    rnoh_demographics = patient.rnohdemographics_set.get()

    rnoh_demographics.rnoh_hospital_number = mrn
    rnoh_demographics.save()

    return patient


def cast_to_SBAR(data, patient):
    """
    Given a dictionary from the upstream database,
    cast to a RNOHSBAR instance.
    """
    sbar = RNOHSBAR(patient=patient)
    for k, v in data.items():
        if v: # Ignore for empty / nullvalues
            setattr(
                sbar,
                RNOHSBAR.UPSTREAM_FIELDS_TO_MODEL_FIELDS[k], v
            )
    return sbar


def load_SBAR():
    """
    Flush and re-load the upstream RNOH SBAR
    """
    api = ProdAPI()

    sbars = api.execute_hospital_query(
        Q_GET_ALL_HANDOVER
    )

    RNOHSBAR.objects.all().delete()

    with transaction.atomic():

        for sbar in sbars:
            patient, _ = get_or_create_RNOH_patient(sbar)

            rnoh_sbar = cast_to_SBAR(sbar, patient)
            rnoh_sbar.save()

            PatientRNOHSBARStatus.objects.get(
                patient=patient).update(
                    has_sbar=True
                )

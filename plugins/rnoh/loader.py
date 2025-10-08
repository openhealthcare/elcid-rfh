"""
Load RNOH Database from upstream.

This is not a BAU process, but a one off import to enable the
decommissioning of the upstream service.

We store the historic RNOH database to maintain access to this clinical
documentation for the team.
"""
import datetime

from django.db import transaction
from django.db.models.functions import Length
from opal.models import Patient

from elcid.models import Demographics
from elcid.episode_categories import InfectionService
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI

from plugins.rnoh.constants import GROUPED_WARD_NAMES, INDIVIDUAL_WARD_NAMES
from plugins.rnoh.episode_categories import RNOHEpisode
from plugins.rnoh.models import PatientRNOHSBARStatus, RNOHSBAR, RNOHDemographics


Q_GET_ALL_HANDOVER = """
SELECT *
FROM HandoverDB.SHIFT_HANDOVERS_X
WHERE
ver = 330697
AND
specialty = 'RNOH'
"""

VIRTUAL_WARD_MAPPING = {
    'New results': 'new_results',
    'Pending ref lab results': 'pending_ref_lab',
    'OPAT': 'opat',
    'Complex OPAT': '',
    'Jobs to action': 'misc',
    'MDT-Upper limb': 'mdt_upper_limb',
}

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

    first, last, dob = data['patient_forename'], data['patient_surname'], data['patient_dob']

    dob = datetime.datetime.strptime(dob, '%d/%m/%Y').date()



    if not mrn.startswith('RAN'):
        raise ValueError(f"{mrn} does not begin with RAN")

    mrn = get_RAN_MRN(mrn)

    # Not always present, but a legit cross-institution identifier, start with this to
    # match with existing elCID patients.
    if data['nhs_number']:
        try:
            demographics = Demographics.objects.get(nhs_number=data['nhs_number'])
            # Write our RNOH upstream demographics.
            # If RFH subsequently insisists on alternate details, this gets
            # set by the PAS integration
            demographics.first_name    = first
            demographics.surname       = last
            demographics.date_of_birth = dob
            demographics.save()

            patient = demographics.patient

            # Ensure they have the appropriate RAN MRN
            rnoh_demographics = patient.rnohdemographics_set.get()

            rnoh_demographics.rnoh_hospital_number = mrn
            rnoh_demographics.save()

            return patient, created
        except Demographics.DoesNotExist:
            pass


    if mrn:
        # Check to see if this patient has already been added to our system,
        # either manually or via this script running previously.
        try:
            demographics = RNOHDemographics.objects.get(rnoh_hospital_number=mrn)
            demographics.first_name    = first
            demographics.surname       = last
            demographics.date_of_birth = dob
            demographics.save()

            return demographics.patient, created
        except RNOHDemographics.DoesNotExist:
            pass


    # Try to match on first, last, DOB.
    # Only attempt a match if all three exist
    if first:
        if last:
            if dob:
                try:
                    demographics = Demographics.objects.get(
                        surname=last, first_name=first, date_of_birth=dob)

                    rnoh_demographics = demographics.patient.rnohdemographics_set.get()

                    rnoh_demographics.rnoh_hospital_number = mrn
                    rnoh_demographics.save()

                    return demographics.patient, created
                except Demographics.DoesNotExist:
                    pass

    # We can't find the patient, create them.
    patient = Patient.objects.create()
    demographics = patient.demographics_set.get()

    demographics.first_name    = first
    demographics.surname       = last
    demographics.date_of_birth = dob
    demographics.save()

    rnoh_demographics = patient.rnohdemographics_set.get()

    rnoh_demographics.rnoh_hospital_number = mrn
    rnoh_demographics.save()

    return patient, created


def cast_to_SBAR(data, patient):
    """
    Given a dictionary from the upstream database,
    cast to a RNOHSBAR instance.
    """
    sbar = RNOHSBAR(patient=patient)
    for k, v in data.items():

        # There is loads of noise here, ignore fields that are never filled
        if k in RNOHSBAR.UPSTREAM_FIELDS_TO_MODEL_FIELDS:

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

    fails = []
    counter = 0

    with transaction.atomic():

        for sbar in sbars:
            counter += 1
            try:
                patient, _ = get_or_create_RNOH_patient(sbar)
                episode, _ = patient.episode_set.get_or_create(category_name=RNOHEpisode.display_name)
                episode, _ = patient.episode_set.get_or_create(category_name=InfectionService.display_name)

                rnoh_sbar = cast_to_SBAR(sbar, patient)

                # We flatten the MRN, but the upstream data uses semantic append to
                # overcome character limitations of text fields in their database.
                # We will require one entry per rf1 number, linked by the base.
                #
                # e.g. MRN 1234 1234A and 1234B should be linked under
                # 1234 on our system, with one RNOHSBAR entry per upstream "MRN"
                #
                sbar_number = sbar['rf1_number']
                existing = RNOHSBAR.objects.filter(patient=patient, mrn=sbar_number).first()

                # The results we get are unfiltered, so check to see if the one we're processing is the
                # longest. If so delete the existing and save it, if not, remove it

                if existing:
                    if len(rnoh_sbar.diagnosis) > len(existing.diagnosis):
                        existing.delete()
                        rnoh_sbar.save()
                    else:
                        continue
                else:
                    rnoh_sbar.save()

                PatientRNOHSBARStatus.objects.filter(
                    patient=patient).update(
                        has_sbar=True
                    )

                # We load the current list onto our current Elcid Patient Lists
                if sbar['discharged'] == 'n':
                    ward, bed = sbar['ward_code'], sbar['bedno']



                    if ward in VIRTUAL_WARD_MAPPING:
                        teams = episode.rnohteams_set.get()
                        setattr(teams, VIRTUAL_WARD_MAPPING[ward], True)
                        teams.save()
                        continue

                    if ward in GROUPED_WARD_NAMES:
                        location = episode.location_set.get()
                        location.hospital = 'RNOH'
                        location.ward = ward
                        location.bed = bed
                        location.save()
                        continue

                    print(f"Can't find {ward}")


            except ValueError:
                fails.append(sbar['rf1_number'])
            except:
                print(f"Uncaught Exception: {sbar['rf1_number']}")
                continue

            print(f"{counter} {sbar['rf1_number']}")

    print(fails)

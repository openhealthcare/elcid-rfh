"""
Management command to load the Excel database
"""
import csv
import datetime
from django.db import transaction

from django.core.management.base import BaseCommand
from django.utils import timezone
from opal.models import Patient, Episode

from plugins.covid import models
from plugins.covid.episode_categories import CovidEpisode


def no_yes(val):
    if val is None or val == "":
        return
    if val == '0':
        return False
    if val == '1':
        return True
    if val == '2':
        return None
    if val in ['No', 'no']:
        return False
    if val in ['Yes', 'yes']:
        return True

    if val == "0 (started on admission)":
        return False

    if val == '1 (?TIA)':
        return True

    # Todo junk
    if val in ['10', '3']:
        return
    if val == 'No thoughts of suicide/self-harm':
        return

    raise ValueError('What is {}'.format(val))


def numeric(val):
    if val is None or val == '':
        return

    # Todo junk
    if val == 'N/A':
        return
    if val == 'Not written':
        return
    if val == 'Unknown due to ITU admission':
        return

    return val


def to_date(val):
    if val == 'N/A':
        return
    # dates come in 2 formats
    # either 01/12/2020
    # or 6/30/20
    val = val.strip()
    if val:
        split = val.split("/")
        if len(split[-1]) == 2:
            return datetime.date(
                int("20{}".format(split[-1])),  # year
                int(split[0]),  # month
                int(split[1])  # day
            )
        else:
            try:
                return datetime.datetime.strptime(
                    val, "%d/%m/%Y"
                ).date()
            except ValueError:
                return datetime.datetime.strptime(
                    val, '%d\\%m\\%Y'
                ).date()


def to_choice(some_numeric, choices):
    """
    Given a value from the data, and a tuple of Django field choices,
    return None or the choice value.

    Assumes the data is 0 indexed.
    """
    if some_numeric in ['5000', '6', '9', '10', 'S']:
        return

    some_numeric = numeric(some_numeric)
    if some_numeric is None:
        return
    if some_numeric:
        try:
            return choices[int(some_numeric)][1]
        except IndexError:
            # Todo junk
            print(some_numeric)
            raise




def tep_status(patient):
    STATUSES = {
        '0': 'Full escalation',
        '1': 'Not for CPR but for ITU',
        '3': 'Not for ITU but for NIV/CPAP',
        '4': 'Not for ITU or CPAP',
        '5': 'Not for ITU, CPAP or NIV'
    }
    value = patient['TEP status: 0 = full escalation, 1= not for CPR but for ITU, 3 = not for ITU but for NIV/CPAP, 4 = not for ITU or CPAP, 5 = not for ITU, CPAP or NIV']
    if value == '':
        return
    if value == 'unknown':
        return
    if value == '?':
        return
    if value == '2':
        return
    return STATUSES[value]


def smoking_status(patient):
    STATUSES = {
        '0': 'Never',
        '1': 'Ex-smoker',
        '2': 'Current',
        '3': 'Unknown'
    }
    value = patient['Smoking status (Never = 0, Ex-smoker = 1, Current = 2, Unknown = 3)']
    if value == '':
        return

    return STATUSES[value]

def ethnicity_code_choice(value):
    CHOICES = {
        '1': 'White',
        '2': 'Black',
        '3': 'Asian',
        '4': 'Other'
    }
    if value == '0':
        return
    if value == '':
        return

    return CHOICES[value]


def max_resp(patient):
    STATUSES = {
        '0': 'No support',
        '1': 'O2',
        '2': 'CPAP',
        '3': 'NIV',
        '4': 'IV'
    }
    field_name = 'Maximum resp support (0=no support, 1 = O2, 2 = CPAP, 3 = NIV, 4 = IV)'
    # This is true if the person went to the emergency department but did not become
    # an inpatient
    value = patient.get(field_name)
    if value is None or value == '':
        return
    if value == 'normally uses NIV':
        return

    return STATUSES[value]


def is_empty(some_value):
    """
    Returns True if some value is none or an empty string
    """
    return some_value is None or some_value == ""


class CSVRow(object):
    """
    The csv in question has duplicate headers, if we
    use a csv DictReader for a csv with
    a,b,a
    1,2,3

    readerRow["a"] will yield 3

    This class will error if you do that and instead you have to say
    reader.get_list("a")[0]

    However it will look like an ordinary csv dict reader for "b"


    It also keeps an internal track of what has been read so you can call
    "get_unread" and it will return you the fields that have not been read.
    """
    def __init__(self, row, headers):
        self.row = row
        self.headers = [i.strip() for i in headers]
        self.duplicates = set()
        self.read = set()
        existing = set()
        for i in self.headers:
            if i in existing:
                self.duplicates.add(i)
            else:
                existing.add(i)

    def get(self, field_name, default_result=None):
        field_name = field_name.strip()
        if field_name not in self.headers:
            return default_result
        else:
            return self[field_name]

    def __getitem__(self, field_name, idx=None):
        field_name = field_name.strip()

        if field_name in self.duplicates:
            raise ValueError("Field {} is a duplicate".format(field_name))

        for num, i in enumerate(self.headers):
            if i == field_name:
                self.read.add(field_name)
                return self.row[num].strip()

        raise ValueError("unable to find {} in csv row".format(field_name))

    def get_list(self, field_name):
        field_name = field_name.strip()
        result = list()
        for num, i in enumerate(self.headers):
            if i == field_name:
                result.append(self.row[num])
        if not result:
            raise ValueError("unable to find list {} in csv row".format(field_name))
        self.read.add(field_name)
        return result

    def get_unread(self):
        return set(self.headers) - self.read


class Command(BaseCommand):
    episodes_created = 0
    admissions_created = 0
    admissions_updated = 0
    followup_calls_created = 0
    missing_mrns = 0
    patient_not_on_elcid = 0

    def add_arguments(self, parser):
        parser.add_argument('file')
        parser.add_argument('--barnet')

    def load_patient(self, patient):

        mrn = patient['Hospital (Internal) Number']
        if not mrn.strip():
            self.missing_mrns += 1
            return False

        try:
            our_patient = Patient.objects.get(demographics__hospital_number=mrn)
            #Todo missing
        except Patient.DoesNotExist:
            self.patient_not_on_elcid += 1
            return False

        try:
            episode, created = our_patient.episode_set.get_or_create(
                category_name=CovidEpisode.display_name
            )
        except Episode.MultipleObjectsReturned:
            print(our_patient)
            raise

        if created:
            self.episodes_created += 1

        # if a patient went to the emergency department but never became an inpatient
        # they have no date of admission
        date_of_admission = patient.get('Date of admission', None)
        try:
            date_of_admission = datetime.datetime.strptime(
                patient['Date of admission'], '%d/%m/%Y %H:%M'
            )
        except ValueError: # Sometimes its just a date
            try:
                date_of_admission = to_date(patient['Date of admission'])
            except ValueError: # And sometimes it junk
                date_of_admission = None

        try:
            date_of_discharge = datetime.datetime.strptime(patient['Date of discharge'], '%d/%m/%Y %H:%M')
        except ValueError:  # Sometimes its just a date
            try:
                date_of_discharge = to_date(patient['Date of discharge'])
            except ValueError: # And sometimes it junk
                date_of_discharge = None

        admission_args = {
            'created_by_id'       : 1,
            'created'             : timezone.now(),
            'date_of_admission'   : date_of_admission,
            'date_of_discharge'   : date_of_discharge,
            'duration_of_symptoms': numeric(patient['Duration of symptoms at admission (days)']),
            'cough'               : no_yes(patient['Symptoms of admission: cough (0 = no, 1 = yes)']),
            'shortness_of_breath' : no_yes(patient['Shortness of breath (0 = no, 1 = yes)']),
            'sore_throat'         : no_yes(patient['Sore throat (0 = no, 1 = yes)']),
            'rhinitis'            : no_yes(patient['Rhinitis (0 = no, 1 = yes)']),
            'fever'               : no_yes(patient['Fever (0 = no, 1 = yes)']),
            'fatigue'             : no_yes(patient['Fatigue (0 = no, 1 = yes)']),
            'myalgia'             : no_yes(patient['Myalgia (0 = no, 1 = yes)']),
            'headache'            : no_yes(patient['Headache (0 = no, 1 = yes)']),
            'anorexia'            : no_yes(patient['Anorexia (0 = no, 1 = yes)']),
            'anosmia'             : no_yes(patient['Anosmia (0 = no, 1 = yes)']),
            'diarrhoea'           : no_yes(patient['Diarrhoea (0 = no, 1 = yes)']),
            'abdominal_pain'      : no_yes(patient['Abdo pain (0 = no, 1 = yes)']),
            'confusion'           : no_yes(patient['Confusion/fuzzy head (0 = no, 1 = yes)']),
            'peripheral_oedema'   : no_yes(patient['Peripheral oedema (0 = no, 1 = yes)']),
            'focal_weakness'      : no_yes(patient['Focal weakness (0 = no, 1 = yes)']),
            'other'               : patient['Other'],
            'predominant_symptom' : patient['Predominant symptom'],
            'respiratory_rate'    : numeric(patient['Respiratory rate on admission (breaths/min)']),
            'heart_rate'          : numeric(patient['Heart rate on admission (beats/min)']),
            'sao2'                : patient['SaO2'],
            'fi02'                : patient['FiO2 (oxygen flow rate if on oxygen)'],
            'systolic_bp'         : numeric(patient['Systolic BP (mmHg)']),
            'diastolic_bp'        : numeric(patient['Diastolic BP (mmHg)']),
            'temperature'         : numeric(patient['Temperature on admission (oC)']),
            'news2'               : patient['NEWS2 score on arrival'],
            'clinical_frailty'    : patient['Clinical frailty score on admission'],
            'tep_status'          : tep_status(patient),
            'maximum_resp_support': max_resp(patient),

            # fields below are not present in the emergency department data when the patient
            # did not become an inpatient
            'days_on_oxygen'      : numeric(patient.get('Total number of days on oxygen')),
            'final_spo2'          : patient.get('Last available SpO2 prior to discharge'),
            'max_fio2_non_nc'     : numeric(patient.get('Max FiO2 (non-NC)')),
            'max_fio2_nc'         : numeric(patient.get('Max FiO2 (if NC)')),
            'systemic_corticosteroirds': no_yes(patient.get('Treated with systemic corticosteroids (0 = no 1 = yes 2 = unknown)')),
        }
        if admission_args["duration_of_symptoms"] == "n/a":
            admission_args["duration_of_symptoms"] = None
            return

        _, created = episode.covidadmission_set.get_or_create()
        if created:
            self.admissions_created += 1
        else:
            self.admissions_updated += 1
        episode.covidadmission_set.update(**admission_args)

        comorbidities = episode.covidcomorbidities_set.get()
        comorbidities.created_by_id = 1
        try:
            comorbidities.hypertension = no_yes(patient["PMH hypertension (No = 0, Yes = 1)"])
        except ValueError:
            comorbidities.hypertension = no_yes(patient["PMH hypertension (No = 0, Yes = 1, Unknown = 2)"])

        comorbidities.ace_inhibitor = no_yes(patient['Current ACEi use (No = 0, Yes = 1, Unknown = 2)'])
        comorbidities.angiotension_blocker = no_yes(patient['Current Angiotension receptor blocker use (No = 0, Yes = 1, Unknown = 2)'])

        nsaid = patient['Current NSAID used (No = 0, Yes = 1, Unknown = 2)']
        if nsaid == '1 diclofenac gel':
            nsaid = True
        else:
            nsaid = no_yes(nsaid)

        comorbidities.nsaid = nsaid

        comorbidities.ihd = no_yes(patient['IHD  (0 = no, 1 = yes)'])
        comorbidities.heart_failure = no_yes(patient['Heart failure  (0 = no, 1 = yes)'])
        comorbidities.arrhythmia = no_yes(patient['AF/arrhythmia  (0 = no, 1 = yes)'])
        comorbidities.cerebrovascular_disease = no_yes(patient['Cerebrovascular disease  (0 = no, 1 = yes)'])
        comorbidities.copd = no_yes(patient['COPD  (0 = no, 1 = yes)'])
        comorbidities.asthma = no_yes(patient['Asthma  (0 = no, 1 = yes)'])
        comorbidities.ild = no_yes(patient['ILD  (0 = no, 1 = yes)'])
        comorbidities.ckd = no_yes(patient['CKD  (0 = no, 1 = yes)'])
        comorbidities.active_malignancy = no_yes(patient['Active malignancy (0=no, 1=yes)'])
        comorbidities.active_malignancy_on_immunosuppression = no_yes(
            patient['Active malignancy on immunosuppression (includes radiotherapy) (1=yes, 0=no)'])

        if patient['HIV  (0 = no, 1 = yes)'] == "n/a":
            comorbidities.hiv = None
        else:
            comorbidities.hiv = no_yes(patient['HIV  (0 = no, 1 = yes)'])
        comorbidities.autoimmunne_with_immunosuppression = no_yes(
            patient['Autoimmune disease requiring current immunosuppression  (0 = no, 1 = yes)'])
        comorbidities.autoimmunne_without_immunosuppression = no_yes(
            patient['Autoimmune disease not requiring current immunosuppression  (0 = no, 1 = yes)'])
        comorbidities.gord = no_yes(patient['GORD  (0 = no, 1 = yes)'])
        comorbidities.depression = no_yes(patient['Depression  (0 = no, 1 = yes)'])
        comorbidities.anxiety = no_yes(patient['Anxiety  (0 = no, 1 = yes)'])

        mental_health = patient['Other mental health disorder  (0 = no, 1 = yes)']
        mental_health_nonsense = [
            '1 (PD, LD)',
            '1 (dementia)'
        ]
        if mental_health in mental_health_nonsense :
            mental_health = True
        else:
            mental_health = no_yes(mental_health)

        comorbidities.other_mental_health = mental_health

        comorbidities.obesity = no_yes(patient['Obesity  (0 = no/unknown, 1 = yes)'])
        comorbidities.save()

        # Covid Follow Up Call

        # If there is no date of telephone call, then the row in the csv is empty
        # skip it.
        if not patient["Date of telephone call"]:
            return

        covid_follow_up_call = models.CovidFollowUpCall(
            episode=episode, created_by_id=1, created=timezone.now(),
            hospital_site=self.hospital_site
        )

        call_date = to_date(patient["Date of telephone call"])
        if call_date:
            call_dt = datetime.datetime.combine(call_date, datetime.time.min)
            covid_follow_up_call.when = timezone.make_aware(call_dt)

        unable_to_complete_reasons = [
            "", "language", "refused", "died", "unreachable", "frail"
        ]
        # This field does not appear in the emergency department csv
        incomplete = patient.get(
            "Unable to complete (1: language 2: refused 3: died 4: unreachable 5:frail)"
        )
        if incomplete:
            if "UCH" in incomplete:
                covid_follow_up_call.incomplete_reason = incomplete
            else:
                covid_follow_up_call.incomplete_reason = to_choice(
                    incomplete, [(i, i) for i in unable_to_complete_reasons]
                )

        covid_follow_up_call.height = patient["Height (m)"]
        covid_follow_up_call.weight = patient["Weight (kg)"]
        covid_follow_up_call.ethnicity = patient.get_list("Ethnicity")[1]


        try:
            covid_follow_up_call.ethnicity_code = ethnicity_code_choice(
                patient["Ethnicity code (White = 1, Black = 2, Asian = 3 Other = 4)"])

        except ValueError:
            try:
                covid_follow_up_call.ethnicity_code = ethnicity_code_choice(
                    patient["Ethnicity code (White = 1, Black = 2 Asian = 3 Other = 4 BrC=1, OC=2, BrA=3, OA=4, BB=5, BO=6, O=7)"])
            except ValueError:
                pass # Barnet doesn't have codings


        covid_follow_up_call.followup_status = to_choice(
            patient["Smoking status (Never = 0, Ex-smoker = 1, Current = 2)"],
            models.SMOKING_CHOICES
        )
        covid_follow_up_call.pack_year_history = patient["Pack year"]

        if patient["Other substances smoked? 0=nothing, 1= vape, 2= other drugs"] == "1":
            covid_follow_up_call.vape = True

        if patient["Other substances smoked? 0=nothing, 1= vape, 2= other drugs"] == "2":
            covid_follow_up_call.other_drugs = True

        social = patient["Social circumstances (0 = independent, 1 = family help, 2 = carers, 3 = NH/RH)"]

        compound_results = set(['1&2', "1,2", "1 & 2"])
        # turn this into carers
        if social in compound_results:
            covid_follow_up_call.social_circumstances = "Independent & family help"
        else:
            covid_follow_up_call.social_circumstances = to_choice(
                social, covid_follow_up_call.CIRCUMSTANCES_CHOICES
            )

        carers = patient["If carers, 1  = OD 2 = BD 3 = TDS 4 = QDS"]

        if carers == '2x/wk + family':
            carers = '1'

        if carers == "24h":
            covid_follow_up_call.carers = carers
        else:
            covid_follow_up_call.carers = to_choice(
                carers, [("", "",)] + list(covid_follow_up_call.CARER_CHOICES)
            )

        try:
            covid_follow_up_call.changes_to_medication = no_yes(
                patient["Any changes in medication since discharge (0 =no, 1 = yes)"]
            )
        except ValueError: # Barnet !
            covid_follow_up_call.changes_to_medication = no_yes(
                patient["Any changes in medication since discharge"]
            )

        covid_follow_up_call.medication_change_details = patient["If yes, what"]

        shielding = patient[
            "Shielding status (0 = not shielding 1 = voluntary 2 = extremely vulnerable 3 = HCP issued letter)"
        ]
        if shielding != 'loss of taste/smell':

            covid_follow_up_call.shielding_status = to_choice(
                shielding, covid_follow_up_call.SHIELDING_CHOICES
            )

        # breathlessness
        covid_follow_up_call.current_breathlessness = patient[
            "Breathlessness rating (0-10)"
        ]
        covid_follow_up_call.max_breathlessness = patient["Max breathlessness"]

        covid_follow_up_call.breathlessness_trend = to_choice(
            patient["Same (0), better (1) or worse (2) than discharge"],
            covid_follow_up_call.TREND_CHOICES
        )

        # cough
        covid_follow_up_call.current_cough = patient["Cough rating (0-10)"]
        covid_follow_up_call.max_cough = patient["Max cough"]
        covid_follow_up_call.cough_trend = to_choice(
            patient["Same (0), better (1) or worse (2) than discharge4"],
            covid_follow_up_call.TREND_CHOICES
        )

        # fatigue
        covid_follow_up_call.current_fatigue = patient["Fatigue rating (0-10)"]
        covid_follow_up_call.max_fatigue = patient["Max fatigue"]

        covid_follow_up_call.fatigue_trend = to_choice(
            patient["Same (0), better (1) or worse (2) than discharge5"],
            covid_follow_up_call.TREND_CHOICES
        )

        # sleep
        covid_follow_up_call.current_sleep_quality = patient[
            "Sleep quality rating (0-10)"
        ]
        covid_follow_up_call.max_sleep_quality = patient["Max sleep quality"]
        covid_follow_up_call.sleep_quality_trend = to_choice(
            patient["Same (0), better (1) or worse (2) than discharge6"],
            covid_follow_up_call.TREND_CHOICES
        )
        covid_follow_up_call.myalgia = no_yes(patient["Myalgia (0 = no 1 = yes)"])
        covid_follow_up_call.anosmia = no_yes(patient["Anosmia (0 = no 1 = yes)"])
        covid_follow_up_call.chest_pain = no_yes(patient["Chest pain (0 = no 1 = yes)"])
        covid_follow_up_call.chest_tightness = no_yes(patient["Chest tightness (0 = no 1 = yes)"])
        covid_follow_up_call.confusion = no_yes(patient["Confusion/fuzzy head (0 = no 1 = yes)"])
        covid_follow_up_call.diarrhoea = no_yes(patient["Diarrhoea (0 = no 1 = yes)"])
        covid_follow_up_call.peripheral_oedema = no_yes(patient["Peripheral oedema (0 = no  yes = 1)"])
        covid_follow_up_call.abdominal_pain = no_yes(patient["Abdo pain (0 = no 1 = yes)"])
        covid_follow_up_call.focal_weakness = no_yes(patient["Focal weakness (0 = no 1  = yes)"])
        try:
            covid_follow_up_call.anorexia = no_yes(patient["Anorexia (0 = no 1 = yes)"])
        except ValueError: # Barnet doesn't have this
            pass
        covid_follow_up_call.back_to_normal = no_yes(patient["Do you feel back to normal (0 = no 1 = yes)"])
        covid_follow_up_call.why_not_back_to_normal = patient["If not, why not"]
        bhp = (numeric(patient[
            "How close to 100% of usual health do you feel"
        ]))

        if bhp in ["Not sure", "prefer not to say", "unsure", 'Feels worse']:
            bhp = None
        elif bhp == "80-85" or bhp == "85-90":
            # skip this and go back and query the source data
            return
        elif bhp is not None and bhp[-1] == "%":
            # sometimes users put a % afterwards, just remove them
            bhp = bhp.replace("%", "")

        if bhp is not None:
            # TODO: Fix these in the source data
            try:
                bhp = int(float(bhp))
            except ValueError:
                return
            covid_follow_up_call.baseline_health_proximity = bhp

        try:
            covid_follow_up_call.back_to_work = to_choice(
                patient["If working are you back to work (Yes = 0 no = 1 N/A = 2)"], covid_follow_up_call.Y_N_NA
            )
        except ValueError: # Barnet
            covid_follow_up_call.back_to_work = to_choice(
                patient["If working are you back to work (Yes = 0 no = 1  n/a = 2)"], covid_follow_up_call.Y_N_NA
            )

        covid_follow_up_call.current_et = patient["Current ET (metres)"]
        covid_follow_up_call.mrc_dyspnoea_scale = patient["MRC dyspnoea scale (1-5)"]


        # common answers include more than one response, e.g. "1,2,3"
        # also users put things like "other({{ what the other is }})"
        limited_by = patient["Limited by (1 = SOB 2 = fatigue 3 = other)"]
        limited_by = limited_by.replace("1", "SOB")
        limited_by = limited_by.replace("2", "Fatigue")
        limited_by = limited_by.replace("3", "Other")
        # make the parenthesis look nicer
        limited_by = limited_by.replace("Other(", "Other (")

        covid_follow_up_call.limited_by = limited_by
        covid_follow_up_call.current_cfs = patient["Current CFS (0-9)"]
        if not is_empty(patient["Little interest/pleasure in doing things (0-3)"]):
            covid_follow_up_call.interest = to_choice(
                patient["Little interest/pleasure in doing things (0-3)"],
                covid_follow_up_call.ZERO_TO_THREE
            )

        if patient["Down, depressed, hopeless (0-3)"] == "4":
            # This is a flaw in the source data
            return

        if not is_empty(patient["Down, depressed, hopeless (0-3)"]):
            covid_follow_up_call.depressed = to_choice(
                patient["Down, depressed, hopeless (0-3)"],
                covid_follow_up_call.ZERO_TO_THREE
            )
        covid_follow_up_call.tsq1 = no_yes(patient["TSQ1 (0 = no 1 = yes)"])
        covid_follow_up_call.tsq2 = no_yes(patient["TSQ2 (0 = no 1 = yes)"])
        covid_follow_up_call.tsq3 = no_yes(patient["TSQ3 (0 = no 1 = yes)"])
        covid_follow_up_call.tsq4 = no_yes(patient["TSQ4 (0 = no 1 = yes)"])
        covid_follow_up_call.tsq5 = no_yes(patient["TSQ5 (0 = no 1 = yes)"])
        covid_follow_up_call.tsq6 = no_yes(patient["TSQ6 (0 = no 1 = yes)"])
        covid_follow_up_call.tsq7 = no_yes(patient["TSQ7 (0 = no 1 = yes)"])
        covid_follow_up_call.tsq8 = no_yes(patient["TSQ8 (0 = no 1 = yes)"])
        covid_follow_up_call.tsq9 = no_yes(patient["TSQ9(0 = no 1 = yes)"])
        covid_follow_up_call.tsq10 = no_yes(patient["TSQ10 (0 = no 1 = yes)"])

        covid_follow_up_call.other_concerns = patient["Other concerns?"]

        NA_Y_N = [('N/A', 'N/A',), ("Yes", "Yes",), ("No", "No",)]
        try:
            covid_follow_up_call.haem_anticoag = to_choice(
                patient["Haematology/anticoagulation clinic (0 = N/A 1 = yes 2 = no)"],
                NA_Y_N
            )
        except ValueError: # Barnet
            covid_follow_up_call.haem_anticoag = to_choice(
                patient["Haematology/anticoagulation clinic (0 = n/a  1 = yes 2 = no)"],
                NA_Y_N
            )

        try:
            covid_follow_up_call.diabetic = to_choice(
                patient["Diabetic team required (0 = n/a 1 = yes 2 = no)"], NA_Y_N
            )
        except ValueError: # Barnet
            covid_follow_up_call.diabetic = to_choice(
                patient["Diabetic team required (0 = n/a  1 = yes 2 = no)"], NA_Y_N
            )


        Y_N_NOT_SURE = [("", ""), ("Yes", "Yes",), ("No", "No",), ("Not Sure", "Not sure",)]
        covid_follow_up_call.call_satisfaction = to_choice(
            patient["Did you find this call useful (1 =yes 2 =no 3=not sure)?"],
            [("", "",)] + list(covid_follow_up_call.Y_N_NOT_SURE)
        )

        covid_follow_up_call.recontact = no_yes(
            patient["Would you be happy to be contacted again (0 = no 1 =yes)?"]
        )
        covid_follow_up_call.save()
        self.followup_calls_created += 1

        return True

    def flush(self):
        models.CovidAdmission.objects.all().delete()
        models.CovidFollowUpCall.objects.all().delete()

    @transaction.atomic
    def handle(self, *args, **kwargs):

        self.hospital_site = 'RFH'
        if 'barnet' in kwargs:
            self.hospital_site = 'Barnet'

        with open(kwargs['file'], 'r') as fh:
            reader = list(csv.reader(fh))
            headers = reader[0]
            rows = reader[1:]
            patients = 0
            imported = 0

            for row in rows:
                patient = CSVRow(row, headers)
                patients += 1

                try:
                    self.load_patient(patient)
                except:
                    print('Patient {} {}'.format(patients, patient['Hospital (Internal) Number']))
                    raise

            print('Patients: {}'.format(patients))
            print(f'Missing MRN: {self.missing_mrns}')
            print(f'Patients not on elCID: {self.patient_not_on_elcid}')
            print('Created episodes: {}'.format(self.episodes_created))
            print('Created admissions: {}'.format(self.admissions_created))
            print('Updated admissions: {}'.format(self.admissions_updated))
            print('Created followups: {}'.format(self.followup_calls_created))
        return

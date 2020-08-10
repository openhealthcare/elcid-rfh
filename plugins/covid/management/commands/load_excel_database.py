"""
Management command to load the Excel database
"""
import csv
import datetime
from django.db import transaction

from django.core.management.base import BaseCommand
from opal.models import Patient, Episode

from plugins.covid import models
from plugins.covid.episode_categories import CovidEpisode


def no_yes(val):
    if val == "":
        return
    if val == '0':
        return False
    if val == '1':
        return True
    if val == '2':
        return None

    if val == "0 (started on admission)":
        return False

    raise ValueError('What is {}'.format(val))


def numeric(val):
    if val == '':
        return
    if val == 'N/A':
        return
    if val == 'Not written':
        return
    return val


def to_date(val):
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
            return datetime.datetime.strptime(
                val, "%d/%m/%Y"
            ).date()


def to_choice(some_numeric, choices):
    """
    choices is of the form of a choice field on a model
    ie a list of tuples
    """
    some_numeric = numeric(some_numeric)
    if some_numeric is None:
        return
    if some_numeric:
        return choices[int(some_numeric)][0]


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


def max_resp(patient):
    STATUSES = {
        '0': 'No support',
        '1': 'O2',
        '2': 'CPAP',
        '3': 'NIV',
        '4': 'IV'
    }
    value = patient['Maximum resp support (0=no support, 1 = O2, 2 = CPAP, 3 = NIV, 4 = IV)']
    if value == '':
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

    def add_arguments(self, parser):
        parser.add_argument('file')

    def load_patient(self, patient):
        mrn = patient['Hospital (Internal) Number']
        if not mrn.strip():
            return False
        try:
            our_patient = Patient.objects.get(demographics__hospital_number=mrn)
        except Patient.DoesNotExist:
            return False

        episode, _ = our_patient.episode_set.get_or_create(category_name=CovidEpisode.display_name)

        try:
            date_of_admission = datetime.datetime.strptime(patient['Date of admission'], '%d/%m/%Y %H:%M')
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
            'episode'             : episode,
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
            'max_fio2_non_nc'     : numeric(patient['Max FiO2 (non-NC)']),
            'max_fio2_nc'         : numeric(patient['Max FiO2 (if NC)']),
            'days_on_oxygen'      : numeric(patient['Total number of days on oxygen']),
            'final_spo2'          : patient['Last available SpO2 prior to discharge'],
            'systemic_corticosteroirds': no_yes(patient['Treated with systemic corticosteroids (0 = no 1 = yes 2 = unknown)']),
        }
        if admission_args["duration_of_symptoms"] == "n/a":
            admission_args["duration_of_symptoms"] = None
            return

        admission, _ = models.CovidAdmission.objects.get_or_create(**admission_args)
        admission.created_by_id = 1
        admission.save()

        # smokinghistory = episode.covidsmokinghistory_set.get()

        # smokinghistory.admisison_status = smoking_status(patient),
        # smokinghistory.pack_year_history = patient['Pack year history']
        # smokinghistory.created_by_id = 1
        # smokinghistory.save()

        # socialhistory, _ = models.CovidSocialHistory.objects.get_or_create(patient=episode.patient, created_by_id=1)

        # CIRCUMSTANCES = {
        #     '0': 'Independent',
        #     '1': 'Family help',
        #     '2': 'Carers',
        #     '3': 'NH/RH'
        # }
        # socialhistory.social_circumstances = CIRCUMSTANCES.get(
        #     patient['Social circumstances (0 = independent, 1 = family help, 2 = carers, 3 = NH/RH)'])

        # CARERS = {
        #     '1': 'OD',
        #     '2': 'BD',
        #     '3': 'TDS',
        #     '4': 'QDS'
        # }
        # carers = patient.get('If carers, 1  = OD 2 = BD 3 = TDS 4 = QDS')
        # if carers:
        #     socialhistory.carers = CARERS.get(carers)

        # shielding = patient.get('Shielding status (0 = not shielding 1 = voluntary 2 = extremely vulnerable 3 = HCP issued letter)')
        # SHIELDING = {
        #     '0': 'Not',
        #     '1': 'Voluntary Shielding',
        #     '2': 'Extremely Vulnerable',
        #     '3': 'Letter Issued by HCP'
        # }
        # socialhistory.shielding_status = SHIELDING.get(shielding)
        # socialhistory.save()

        comorbidities = episode.covidcomorbidities_set.get()
        comorbidities.created_by_id = 1
        comorbidities.hypertension = no_yes(patient['PMH hypertension (No = 0, Yes = 1, Unknown = 2)'])
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
        covid_follow_up_call = models.CovidFollowUpCall(episode=episode)

        # If there is no date of telephone call, then the row in the csv is empty
        # skip it.
        if not patient["Date of telephone call"]:
            return

        covid_follow_up_call.when = to_date(patient["Date of telephone call"])
        unable_to_complete_reasons = [
            "", "language", "refused", "died", "unreachable", "frail"
        ]
        incomplete = patient[
            "Unable to complete (1: language 2: refused 3: died 4: unreachable 5:frail)"
        ]
        if "UCH" in incomplete:
            covid_follow_up_call.incomplete_reason = incomplete
        else:
            covid_follow_up_call.incomplete_reason = to_choice(
                incomplete, [(i, i) for i in unable_to_complete_reasons]
            )

        covid_follow_up_call.height = patient["Height (m)"]
        covid_follow_up_call.weight = patient["Weight (kg)"]
        covid_follow_up_call.ethnicity = patient.get_list("Ethnicity")[1]

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

        compound_results = set(['1&2', "1,2"])
        # turn this into carers
        if social in compound_results:
            covid_follow_up_call.social_circumstances = "Independent & family help"
        else:
            covid_follow_up_call.social_circumstances = to_choice(
                social, covid_follow_up_call.CIRCUMSTANCES_CHOICES
            )

        carers = patient["If carers, 1  = OD 2 = BD 3 = TDS 4 = QDS"]

        if carers == "24h":
            covid_follow_up_call.carers = carers
        else:
            covid_follow_up_call.carers = to_choice(
                carers, [("", "",)] + list(covid_follow_up_call.CARER_CHOICES)
            )

        covid_follow_up_call.changes_to_medication = no_yes(
            patient["Any changes in medication since discharge (0 =no, 1 = yes)"]
        )
        covid_follow_up_call.medication_change_details = patient["If yes, what"]

        shielding = patient[
            "Shielding status (0 = not shielding 1 = voluntary 2 = extremely vulnerable 3 = HCP issued letter)"
        ]
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
        covid_follow_up_call.anorexia = no_yes(patient["Anorexia (0 = no 1 = yes)"])
        covid_follow_up_call.back_to_normal = no_yes(patient["Do you feel back to normal (0 = no 1 = yes)"])
        covid_follow_up_call.why_not_back_to_normal = patient["If not, why not"]
        bhp = (numeric(patient[
            "How close to 100% of usual health do you feel"
        ]))

        if bhp in ["Not sure", "prefer not to say"]:
            bhp = None
        elif bhp == "80-85":
            # skip this and go back and query the source data
            return
        elif bhp is not None and bhp[-1] == "%":
            # sometimes users put a % afterwards, just remove them
            bhp = bhp.replace("%", "")

        if bhp is not None:
            covid_follow_up_call.baseline_health_proximity = int(float(bhp))

        covid_follow_up_call.back_to_work = to_choice(
            patient["If working are you back to work (Yes = 0 no = 1 N/A = 2)"], covid_follow_up_call.Y_N_NA
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
        covid_follow_up_call.haem_anticoag = to_choice(
            patient["Haematology/anticoagulation clinic (0 = N/A 1 = yes 2 = no)"],
            NA_Y_N
        )
        covid_follow_up_call.diabetic = to_choice(
            patient["Diabetic team required (0 = n/a 1 = yes 2 = no)"], NA_Y_N
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

        print('{} {}'.format(str(our_patient), our_patient.demographics().hospital_number))
        return True

    def flush(self):
        Episode.objects.filter(category_name=CovidEpisode.display_name).delete()

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.flush()

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
                    raise

            print('Patients: {}'.format(patients))
            print('Imported episodes: {}'.format(
                Episode.objects.filter(
                    category_name=CovidEpisode.display_name
                ).count()
            ))
            print('Imported admissions: {}'.format(
                models.CovidAdmission.objects.objects.all().count()
            ))
            print('Imported follow up calls: {}'.format(
                models.CovidFollowUpCall.objects.all().count()
            ))


        return

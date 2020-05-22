"""
Management command to load the Excel database
"""
import csv
import datetime
import traceback

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
    raise ValueError('What is {}'.format(val))


def numeric(val):
    if val == '':
        return
    if val == 'N/A':
        return
    if val == 'Not written':
        return
    return val


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


class Command(BaseCommand):


    def load_patient(self, patient):
        mrn = patient['Hospital (Internal) Number']
        try:
            our_patient = Patient.objects.get(demographics__hospital_number=mrn)
        except Patient.DoesNotExist:
            return False

        episode, _ = our_patient.episode_set.get_or_create(category_name=CovidEpisode.display_name)

        try:
            date_of_admission = datetime.datetime.strptime(patient['Date of admission'], '%d/%m/%Y %H:%M')
        except ValueError: # Junk in the raw data
            date_of_admission = None

        try:
            date_of_discharge = datetime.datetime.strptime(patient['Date of discharge'], '%d/%m/%Y %H:%M')
        except ValueError: # Junk in the raw data
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
            'height'              : patient['Height (m)'],
            'weight'              : patient['Weight (kg)'],
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
            'smoking_status'      : smoking_status(patient),
            'maximum_resp_support': max_resp(patient),
            'max_fio2_non_nc'     : numeric(patient['Max FiO2 (non-NC)']),
            'max_fio2_nc'         : numeric(patient['Max FiO2 (if NC)']),
            'days_on_oxygen'      : numeric(patient['Total number of days on oxygen']),
            'final_spo2'          : patient['Last available SpO2 prior to discharge'],
            'systemic_corticosteroirds': no_yes(patient['Treated with systemic corticosteroids (0 = no 1 = yes 2 = unknown)']),
        }
        admission, _ = models.CovidAdmission.objects.get_or_create(**admission_args)
        admission.created_by_id = 1
        admission.save()

        if patient['Pack year history']:
           smokinghistory = episode.covidsmokinghistory_set.get()
           smokinghistory.pack_year_history = patient['Pack year history']
           smokinghistory.created_by_id = 1
           smokinghistory.save()

        socialhistory, _ = models.CovidSocialHistory.objects.get_or_create(patient=episode.patient, created_by_id=1)

        CIRCUMSTANCES = {
            '0': 'Independent',
            '1': 'Family help',
            '2': 'Carers',
            '3': 'NH/RH'
        }
        socialhistory.social_circumstances = CIRCUMSTANCES.get(
            patient['Social circumstances (0 = independent, 1 = family help, 2 = carers, 3 = NH/RH)'])

        CARERS = {
            '1': 'OD',
            '2': 'BD',
            '3': 'TDS',
            '4': 'QDS'
        }
        carers = patient.get('If carers, 1  = OD 2 = BD 3 = TDS 4 = QDS')
        if carers:
            socialhistory.carers = CARERS[carers]

        shielding = patient.get('Shielding status (0 = not shielding 1 = voluntary 2 = extremely vulnerable 3 = HCP issued letter)')
        SHIELDING = {
            '0': 'Not',
            '1': 'Voluntary Shielding',
            '2': 'Extremely Vulnerable',
            '3': 'Letter Issued by HCP'
        }
        socialhistory.shielding_status = SHIELDING.get(shielding)
        socialhistory.save()

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

        print('{} {}'.format(str(our_patient), our_patient.demographics().hospital_number))
        return True

    def flush(self):
        Episode.objects.filter(category_name=CovidEpisode.display_name).delete()

    def handle(self, *args, **kwargs):
        self.flush()

        with open('/Users/david/src/ohc/data/COVID-19/Database-Table 1.csv', 'r') as fh:
            reader = csv.DictReader(fh)
            patients = 0
            imported = 0

            for patient in reader:
                patients += 1
                try:
                    worked = self.load_patient(patient)
                    if worked:
                        imported += 1
                except:
                    raise

            print('Patients: {}'.format(patients))
            print('Imported: {}'.format(imported))


        return

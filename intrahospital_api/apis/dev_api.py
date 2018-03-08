from django.conf import settings
from intrahospital_api.apis import base_api
from datetime import date, timedelta, datetime
from elcid import models as emodels
from lab import models as lmodels
import random

RAW_DATA = {
    u'Abnormal_Flag': u'',
    u'Accession_number': u'73151060487',
    u'CRS_ADDRESS_LINE1': u'Jameson Centre',
    u'CRS_ADDRESS_LINE2': u'39 Windsor Terrace',
    u'CRS_ADDRESS_LINE3': u'LONDON',
    u'CRS_ADDRESS_LINE4': u'',
    u'CRS_DOB': datetime(1980, 10, 10, 0, 0),
    u'CRS_Date_of_Death': datetime(1900, 1, 1, 0, 0),
    u'CRS_Deceased_Flag': u'ALIVE',
    u'CRS_EMAIL': u'',
    u'CRS_Ethnic_Group': u'D',
    u'CRS_Forename1': u'TEST',
    u'CRS_Forename2': u'',
    u'CRS_GP_NATIONAL_CODE': u'G1005756',
    u'CRS_GP_PRACTICE_CODE': u'H85012',
    u'CRS_HOME_TELEPHONE': u'0111111111',
    u'CRS_MAIN_LANGUAGE': u'',
    u'CRS_MARITAL_STATUS': u'',
    u'CRS_MOBILE_TELEPHONE': u'',
    u'CRS_NATIONALITY': u'GBR',
    u'CRS_NHS_Number': u'',
    u'CRS_NOK_ADDRESS1': u'',
    u'CRS_NOK_ADDRESS2': u'',
    u'CRS_NOK_ADDRESS3': u'',
    u'CRS_NOK_ADDRESS4': u'',
    u'CRS_NOK_FORENAME1': u'',
    u'CRS_NOK_FORENAME2': u'',
    u'CRS_NOK_HOME_TELEPHONE': u'',
    u'CRS_NOK_MOBILE_TELEPHONE': u'',
    u'CRS_NOK_POST_CODE': u'',
    u'CRS_NOK_RELATIONSHIP': u'',
    u'CRS_NOK_SURNAME': u'',
    u'CRS_NOK_TYPE': u'',
    u'CRS_NOK_WORK_TELEPHONE': u'',
    u'CRS_Postcode': u'N6 P12',
    u'CRS_Religion': u'',
    u'CRS_SEX': u'F',
    u'CRS_Surname': u'ZZZTEST',
    u'CRS_Title': u'',
    u'CRS_WORK_TELEPHONE': u'',
    u'DOB': datetime(1964, 1, 1, 0, 0),
    u'Date_Last_Obs_Normal': datetime(2015, 7, 18, 16, 26),
    u'Date_of_the_Observation': datetime(2015, 7, 18, 16, 26),
    u'Department': u'9',
    u'Encounter_Consultant_Code': u'C2754019',
    u'Encounter_Consultant_Name': u'DR. M. SMITH',
    u'Encounter_Consultant_Type': u'',
    u'Encounter_Location_Code': u'6N',
    u'Encounter_Location_Name': u'RAL 6 NORTH',
    u'Encounter_Location_Type': u'IP',
    u'Event_Date': datetime(2015, 7, 18, 16, 47),
    u'Firstname': u'TEST',
    u'MSH_Control_ID': u'18498139',
    u'OBR-5_Priority': u'N',
    u'OBR_Sequence_ID': u'2',
    u'OBR_Status': u'F',
    u'OBR_exam_code_ID': u'ANNR',
    u'OBR_exam_code_Text': u'ANTI NEURONAL AB REFERRAL',
    u'OBX_Sequence_ID': u'11',
    u'OBX_Status': u'F',
    u'OBX_exam_code_ID': u'AN12',
    u'OBX_exam_code_Text': u'Anti-CV2 (CRMP-5) antibodies',
    u'OBX_id': 20334311,
    u'ORC-9_Datetime_of_Transaction': datetime(2015, 7, 18, 16, 47),
    u'Observation_date': datetime(2015, 7, 18, 16, 18),
    u'Order_Number': u'',
    u'Patient_Class': u'NHS',
    u'Patient_ID_External': u'7060976728',
    u'Patient_Number': u'20552710',
    u'Relevant_Clinical_Info': u'testing',
    u'Reported_date': datetime(2015, 7, 18, 16, 26),
    u'Request_Date': datetime(2015, 7, 18, 16, 15),
    u'Requesting_Clinician': u'C4369059_Claire Jameson',
    u'Result_ID': u'0013I245895',
    u'Result_Range': u' -',
    u'Result_Units': u'',
    u'Result_Value': u'Negative',
    u'SEX': u'F',
    u'Specimen_Site': u'^&                              ^',
    u'Surname': u'ZZZTEST',
    u'Visit_Number': u'',
    u'crs_patient_masterfile_id': None,
    u'date_inserted': datetime(2015, 7, 18, 17, 0, 2, 240000),
    u'id': 5949264,
    u'last_updated': datetime(2015, 7, 18, 17, 0, 2, 240000),
    u'visible': u'Y'
}


MALE_FIRST_NAMES = [
    'Harry', 'Ron', 'Tom', 'Albus', 'Severus', 'Rubeus', 'Draco',
]

FEMALE_FIRST_NAMES = [
    'Hermione', 'Minerva', 'Padma', 'Parvati', 'Lilly', 'Rita', 'Rowena'
]

LAST_NAMES = [
    'Potter', 'Granger', 'Weasley', 'Malfoy', 'Dumbledore', 'Gryffindor',
    'Greyback', 'Filch', 'Diggory', 'McGonagall'
]

# So this is basic meta information about some tests that come through
# we will then use this to create mock results
TEST_BASES = {
    "B12 AND FOLATE SCREEN": {
        "Vitamin B12": {
            "reference_range": "160 - 925",
            "units": "ng/L"
        },
        "Folate": {
            "reference_range": "3.9 - 26.8",
            "units": "ng/L"
        }
    },
    "C REACTIVE PROTEIN": {
        "C Reactive Protein": {
            "units": "mg/L",
            "reference_range": "0 - 5"
        }
    },
    "FULL BLOOD COUNT": {
        "Hb": {
            "units": "g/l",
            "reference_range": "110 - 150"
        },
        "WBC": {
            "units": "g/l",
            "reference_range": "3.5 - 11"
        },
        "Platelets": {
            "units": "10",
            "reference_range": "140 - 400"
        },
        "RBC": {
            "units": "10",
            "reference_range": "3.8 - 5.4"
        },
        "HCT": {
            "units": "%",
            "reference_range": "11 - 16"
        },
        "Lymphocytes": {
            "units": "10",
            "reference_range": "1 - 4"
        },
        "Neutrophils": {
            "units": "10",
            "reference_range": "1.7 - 7.5"
        }
    },
    "CLOTTING_SCREEN": {
        "INR": {
            "units": "Ratio",
            "reference_range": "0.9 - 1.12"
        }
    },
    "LIVER PROFILE": {
        "ALT": {
            "units": "U/L",
            "reference_range": "10 - 35"
        },
        "AST": {
            "units": "U/L",
            "reference_range": "0 - 31"
        },
        "Alkaline Phosphatase": {
            "units": "U/L",
            "reference_range": "0 - 129"
        }
    }
}


class DevApi(base_api.BaseApi):
    def get_date_of_birth(self):
        return date.today() - timedelta(random.randint(1, 365 * 70))

    def demographics(self, hospital_number):
        # will always be found unless you prefix it with 'x'
        if hospital_number.startswith('x'):
            return

        sex = random.choice(["Male", "Female"])
        if sex == "Male":
            first_name = random.choice(MALE_FIRST_NAMES)
            title = random.choice(["Dr", "Mr", "Not Specified"])
        else:
            first_name = random.choice(FEMALE_FIRST_NAMES)
            title = random.choice(["Dr", "Ms", "Mrs", "Not Specified"])

        return dict(
            date_of_birth=self.get_date_of_birth(),
            ethnicity="Other",
            external_system="DEV_API",
            first_name=first_name,
            hospital_number=hospital_number,
            nhs_number=self.get_external_identifier(),
            sex=sex,
            surname=random.choice(LAST_NAMES),
            title=title
        )

    def get_external_identifier(self):
        random_str = str(random.randint(0, 100000000))
        return "{}{}".format("0" * (9-len(random_str)), random_str)

    def get_observation_value(self, reference_range):
        """
            splits the reference range, casts it to an integer
            returns a result around those boundaries
        """
        min_result, max_result = [
            float(i.strip()) for i in reference_range.split("-")
        ]
        acceptable_range = max_result - min_result
        random_result = round(random.uniform(min_result, acceptable_range), 1)
        deviation = round(random.uniform(acceptable_range/3, acceptable_range))
        plus_minus = random.randint(0, 1)

        if plus_minus:
            return random_result + deviation
        else:
            return random_result - deviation

    def cooked_data(self, hospital_number):
        rows = []
        demographics = self.demographics(hospital_number)
        results = self.results_for_hospital_number(hospital_number)
        for result in results:
            for obs in result["observations"]:
                row = {}
                row.update(
                    {i: v for i, v in obs.items() if i != 'observations'}
                )
                row.update(obs)
                row.update(demographics)
                rows.append(row)

        return rows

    def create_observation_dict(
        self,
        test_base_observation_name,
        test_base_observation_value,
        base_datetime=None
    ):
        """
        should return something like...
        {
            "last_updated": "18 Jul 2019, 4:18 p.m.",
            "observation_datetime": "18 Jul 2015, 4:18 p.m."
            "observation_name": "Aerobic bottle culture",
            "observation_number": "12312",
            "reference_range": "3.5 - 11",
            "units": "g"
        }

        """
        if base_datetime is None:
            base_datetime = datetime.now()

        return dict(
            last_updated=(base_datetime - timedelta(minutes=20)).strftime(
                '%d/%m/%Y %H:%M:%S'
            ),
            observation_datetime=(base_datetime - timedelta(1)).strftime(
                '%d/%m/%Y %H:%M:%S'
            ),
            observation_name=test_base_observation_name,
            observation_number=self.get_external_identifier(),
            observation_value=str(self.get_observation_value(
                test_base_observation_value["reference_range"]
            )),
            reference_range=test_base_observation_value["reference_range"],
            units=test_base_observation_value["units"],
        )

    def results_for_hospital_number(self, hospital_number, **filter_kwargs):
        """ We expect a return of something like
            {
                clinical_info:  u'testing',
                datetime_ordered: "18 Jul 2015, 4:15 p.m.",
                external_identifier: "ANTI NEURONAL AB REFERRAL",
                site: u'^&                              ^',
                status: "Sucess",
                test_code: "AN12"
                test_name: "Anti-CV2 (CRMP-5) antibodies",
                observations: [{
                    "last_updated": "18 Jul 2019, 4:18 p.m.",
                    "observation_datetime": "18 Jul 2015, 4:18 p.m."
                    "observation_name": "Aerobic bottle culture",
                    "observation_number": "12312",
                    "reference_range": "3.5 - 11",
                    "units": "g"
                }]
            }
        """
        result = []
        for i, v in TEST_BASES.items():
            for date_t in range(10):
                base_datetime = datetime.now() - timedelta(date_t)
                result.append(dict(
                    clinical_info=u'testing',
                    datetime_ordered=base_datetime.strftime(
                        '%d/%m/%Y %H:%M:%S'
                    ),
                    external_identifier=self.get_external_identifier(),
                    status=lmodels.LabTest.COMPLETE,
                    site=u'^&                              ^',
                    test_code=i.lower().replace(" ", "_"),
                    test_name=i,
                    observations=[
                        self.create_observation_dict(
                            o, y, base_datetime=base_datetime
                        ) for o, y in v.items()
                    ]
                ))

        return result

    def raw_data(self, hospital_number, **filter_kwargs):
        return [RAW_DATA]

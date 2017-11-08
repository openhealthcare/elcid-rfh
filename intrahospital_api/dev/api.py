from django.conf import settings
from intrahospital_api.base import api
from datetime import date, timedelta, datetime
from elcid import models as emodels
from lab import models as lmodels
import random

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
            "reference_range": "110 - 150"
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


class DevApi(api.BaseApi):
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
            sex=sex,
            date_of_birth=self.get_date_of_birth(),
            first_name=first_name,
            surname=random.choice(LAST_NAMES),
            title=title,
            hospital_number=hospital_number,
            external_system="DEV_API"
        )

    def results(self, hospital_number):
        """
            creates random mock lab tests, all tests created will be for the
            last 10 days... just because (this could be more realistic...)
        """
        now = datetime.now()
        result = []
        for i in range(10):
            old_news = now - timedelta(i)
            for lab_test_type in TEST_BASES.keys():
                result.append(
                    self.create_lab_test(
                        lab_test_type, old_news
                    )
                )
        return result

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

    def create_lab_test(
        self,
        lab_test_type,
        datetime_ordered,
        result_status=lmodels.LabTest.COMPLETE
    ):
        external_identifier = self.get_external_identifier()
        datetime_ordered_str = datetime_ordered.strftime(
            settings.DATETIME_INPUT_FORMATS[0]
        )

        observations = TEST_BASES.get(lab_test_type)
        result = dict(
            extras=dict(
                observation_datetime=datetime_ordered_str,
                profile_description=lab_test_type,
                last_edited=datetime_ordered_str,
            ),
            external_identifier=external_identifier,
            datetime_ordered=datetime_ordered_str,
            lab_test_type=emodels.HL7Result.get_display_name(),
            status=result_status,
            observations=[]
        )
        for test_name, fields in observations.items():
            reference_range = fields["reference_range"]
            result["observations"].append(dict(
                test_name=test_name,
                result_status="Final",
                observation_value=str(
                    self.get_observation_value(reference_range)
                ),
                reference_range=reference_range,
                units=fields["units"]
            ))
        return result

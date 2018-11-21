import random
from datetime import date, timedelta, datetime
from intrahospital_api import constants

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


class Backend(object):

    def get_date_of_birth(self):
        some_date = date.today() - timedelta(random.randint(1, 365 * 70))
        some_dt = datetime.combine(
            some_date, datetime.min.time()
        )
        return some_dt.strftime('%d/%m/%Y')

    def get_external_identifier(self):
        random_str = str(random.randint(0, 100000000))
        return "{}{}".format("0" * (9-len(random_str)), random_str)

    def demographics_for_hospital_number(self, hospital_number):
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
            external_system=constants.EXTERNAL_SYSTEM,
            first_name=first_name,
            hospital_number=hospital_number,
            nhs_number=self.get_external_identifier(),
            sex=sex,
            surname=random.choice(LAST_NAMES),
            title=title
        )

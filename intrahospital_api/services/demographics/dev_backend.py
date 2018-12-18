import random
from datetime import date, timedelta, datetime
from intrahospital_api import constants

MALE_FIRST_NAMES = [
    'Werner',
    'Scott',
    'Fred',
    'Irving',
    'Donovan',
    'Josef',
    'Danial',
    'Eli',
    'Kermit',
    'Sammy',
    'Claude',
    'Rueben',
    'Trenton',
    'Cliff',
    'Sean',
    'Rufus',
    'Graham',
    'Tracy',
    'Neville',
    'Dion'
]

FEMALE_FIRST_NAMES = [
    'Wai',
    'Mardell',
    'Jodie',
    'Edith',
    'Ola',
    'Geralyn',
    'Delcie',
    'Cathy',
    'Mafalda',
    'Mayme',
    'Lanette',
    'Heidi',
    'Ana',
    'Nydia',
    'Rosalie',
    'Rosann',
    'Corrin',
    'Janene',
    'Kathlene',
    'Irene'
]

LAST_NAMES = [
    'Smith',
    'Jones',
    'Taylor',
    'Brown',
    'Williams',
    'Wilson',
    'Johnson',
    'Davies',
    'Robinson',
    'Wright',
    'Thompson',
    'Evans',
    'Walker',
    'White',
    'Roberts',
    'Green',
    'Hall',
    'Wood',
    'Jackson',
    'Clarke'
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

    def fetch_for_identifier(self, identifier):
        # will always be found unless you prefix it with 'x'
        if identifier.startswith('x'):
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
            hospital_number=identifier,
            nhs_number=self.get_external_identifier(),
            sex=sex,
            surname=random.choice(LAST_NAMES),
            title=title
        )

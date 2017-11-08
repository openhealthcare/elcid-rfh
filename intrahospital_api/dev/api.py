from intrahospital_api.base import api
from datetime import date, timedelta
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
            hospital_number=hospital_number
        )

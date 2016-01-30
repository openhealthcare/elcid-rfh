import datetime

from opal.core.patient_lists import PatientList, TaggedPatientList
from opal.models import Patient, Episode
from elcid import models

ibd_schema = [
    models.Demographics
]

class PatientsDueBloods(TaggedPatientList):
    tag = "duebloods"
    schema = ibd_schema

    def get_queryset(self):
        in_one_week = datetime.date.today() + datetime.timedelta(days=7)
        episodes = Episode.objects.filter(ibdinfo__next_blood__lte=in_one_week)
        print episodes
        return episodes


class PatientsOverdueBloods(TaggedPatientList):
    tag = "overduebloods"
    schema = ibd_schema


class ResultsBack(TaggedPatientList):
    tag = "resultsback"
    schema = ibd_schema

"""
TEMPORARY SOLUTION

We will hard refresh upstream data for
all patients currently on ICU. This is a temporary measure
during hte Covid 19 '2nd wave'.
"""
import traceback

from django.core.management.base import BaseCommand

from plugins.admissions.loader import load_encounters
from plugins.appointments.loader import load_appointments
from plugins.dischargesummary.loader import load_dischargesummaries

from plugins.icu import logger, models

class Command(BaseCommand):
    def handle(self, *a, **k):
        try:
            icu_patients = [i.patient for i in models.ICUHandoverLocation.objects.all()]

            for patient in icu_patients:
                load_dischargesummaries(patient)
                load_encounters(patient)
                load_appointments(patient)

        except:
            msg = 'Exception hard refreshing ICU Handover Patients \n {}'
            logger.error(msg.format(traceback.format_exc()))
        return

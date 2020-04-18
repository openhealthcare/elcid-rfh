"""
Management command to fetch all appointments for our patients
"""
import traceback

from django.core.management import BaseCommand

from elcid.models import Demographics

from plugins.appointments import loader, logger


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for demographic in Demographics.objects.all():
            try:
                patient = demographic.patient
                loader.load_appointments(patient)
            except:
                msg = 'Exception loading ICU Handover Patients \n {}'
                logger.error(msg.format(traceback.format_exc()))
        return

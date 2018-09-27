import datetime
from django.core.management.base import BaseCommand
from intrahospital_api import models


class Command(BaseCommand):
    def min_datetime(self, date):
        return datetime.datetime.combine(date, datetime.time.min)

    def todays_initial_patient_loads(self):
        today = datetime.datetime.today()
        return models.InitialPatientLoad.objects.filter(
            start__gte=self.min_datetime(today),
        )

    def todays_batch_patient_loads(self):
        today = datetime.datetime.today()
        return models.BatchPatientLoad.objects.filter(
            start__gte=self.min_datetime(today),
        )

    def nothing_long_running(self, qs, amount):
        """
        A qs should not be more long running that { amount }

        e.g. no initial patient load should last longer than 10 mins

        no lab test batch load should last longer than { amount }
        """
        pass

    def patients_should_have_been_added(self):
        """
        We expect at least one patient to have been added every day
        """
        pass

    def amount_of_batch_runs_that_should_have_run(self, qs, amount):
        """
        We expect at least {amount} batch runs to run on a daily basis
        """
        pass

    def amount_of_lab_tests_that_should_have_loaded(self):
        """
        At least some lab tests not including Initial Patient Loads
        should have loaded.
        """
        pass


    def handle(self, *args, **options):
        patients = models.Initia

        # We expect at least one patient to be added per day

        # We expect at least some lab tests to be loaded for
        # patients that have InitialPatientLoads

        # We expect BatchPatientLoads to load in at least some
        # lab tests in a day
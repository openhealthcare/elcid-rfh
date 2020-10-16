"""
Management command to look and see if patients have follow up
appointments upstream and if so to create those patients
"""
from django.core.management.base import BaseCommand
from opal.models import Patient

from plugins.covid import loader
from plugins.covid.episode_categories import CovidEpisode


class Command(BaseCommand):

    def handle(self, *args, **options):
        loader.create_followup_episodes()

        without_followups = Patient.objects.filter(
            covid_patient__date_first_positive__isnull=False
        ).exclude(episode__category_name=CovidEpisode.display_name).count()

        for patient in without_followups:
            patient.create_episode(category_name=CovidEpisode.display_name)

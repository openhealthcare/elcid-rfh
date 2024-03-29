"""
Unittests for elcid.management.commands.status_report
"""
import datetime
import logging
import json
from unittest import mock

from django.utils import timezone
from opal.core.test import OpalTestCase

from elcid.management.commands import status_report


class RandomiseStatusReport(OpalTestCase):

    def test_handle_subrecords(self):
        """ it should return a dump of all subrecords from the last year
            and all subrecords from the last week
        """
        patient, episode = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name="Wilma",
            surname="Flintstone",
            created=timezone.make_aware(datetime.datetime(2015, 1, 1))
        )

        patient.riskfactor_set.create(
            created=timezone.now() - datetime.timedelta(1)
        )

        command = status_report.Command()
        with mock.patch.object(command, 'stdout') as stdout:
            command.handle()
        output = json.loads(stdout.write.call_args[0][0])

        self.assertEqual(
            output["all_time"]["Demographics"], 1
        )

        # 0 because the demographics were not created in the last week
        self.assertEqual(
            output["last_week"]["Demographics"], 0
        )
        self.assertEqual(
            output["all_time"]["Risk Factors"], 1
        )
        self.assertEqual(
            output["last_week"]["Risk Factors"], 1
        )

    def test_handle_episodes(self):
        """ it should return a dump of all subrecords from the last year
            and all subrecords from the last week
        """
        patient, episode = self.new_patient_and_episode_please()

        command = status_report.Command()
        with mock.patch.object(command, 'stdout') as stdout:
            command.handle()
        output = json.loads(stdout.write.call_args[0][0])

        self.assertEqual(
            output["all_time"]["Episode"], 1
        )

        # 0 because the episode does not have a created date
        self.assertEqual(
            output["last_week"]["Episode"], 0
        )

    @mock.patch('elcid.management.commands.status_report.logging.getLogger')
    def test_set_logger_to_error(self, get_logger):
        command = status_report.Command()
        # lets stop unnecessary printing
        with mock.patch.object(command, 'stdout'):
            command.handle()
        get_logger().setLevel.assert_called_once_with(logging.ERROR)

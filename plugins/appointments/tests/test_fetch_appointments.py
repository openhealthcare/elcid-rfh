"""
Unittests for the fetch_appointments management command
"""
from unittest import mock

from opal.core.test import OpalTestCase

from plugins.appointments.management.commands import fetch_appointments


class CommandTestCase(OpalTestCase):

    def test_wont_raise(self):
        self.new_patient_and_episode_please()

        command = fetch_appointments.Command()

        with mock.patch.object(fetch_appointments.loader, 'load_appointments') as load:
            with mock.patch('plugins.appointments.logger.error'): # shhh
                load.side_effect = Exception('Boom!')
                command.handle()

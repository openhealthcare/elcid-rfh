"""
Unittests for the load_icu_handover_patients management command
"""
from unittest import mock

from opal.core.test import OpalTestCase

from plugins.icu.management.commands import load_icu_handover_patients


class CommandTestCase(OpalTestCase):

    def test_wont_raise(self):

        command = load_icu_handover_patients.Command()

        with mock.patch.object(load_icu_handover_patients.loader, 'load_icu_handover') as load:
            with mock.patch('plugins.icu.logger.error'): # shhh
                load.side_effect = Exception('Boom!')
                command.handle()

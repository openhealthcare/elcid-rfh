"""
Unittests for the module plugins.admissions.management.commands.fetch_admissions
"""
from unittest import mock

from opal.core.test import OpalTestCase

from plugins.monitoring.models import Fact

from plugins.admissions.management.commands import fetch_admissions


class CommandTestCase(OpalTestCase):

    def test_creates_facts(self):
        self.assertEqual(0, Fact.objects.all().count())

        with mock.patch.object(fetch_admissions.loader, 'load_excounters_since'):
            cmd = fetch_admissions.Command()
            cmd.handle()
            self.assertEqual(2, Fact.objects.all().count())

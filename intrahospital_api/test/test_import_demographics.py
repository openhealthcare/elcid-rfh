import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands.import_demographics import Command


@mock.patch(
    'intrahospital_api.management.commands.import_demographics.update_external_demographics'
)
class ImportDemographicsTestCase(OpalTestCase):
    def test_handle(self, update_external_demographics):
        Command().handle()
        update_external_demographics.called_once_with()

import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import smoke_check


@mock.patch(
    "intrahospital_api.management.commands.smoke_check.smoke_check.check_loads"
)
class SmokeCheckTestCase(OpalTestCase):
    def test_call_through(self, check_loads):
        command = smoke_check.Command()
        command.handle()
        check_loads.assert_called_once_with()
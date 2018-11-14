import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import smoke_test


@mock.patch(
    "intrahospital_api.management.commands.smoke_test.service.smoke_test"
)
class SmokeTestTestCase(OpalTestCase):
    def setUp(self):
        super(SmokeTestTestCase, self).setUp()
        self.handle = smoke_test.Command().handle

    def test_batch_appointments_load(self, sm):
        self.handle()
        self.assertTrue(
            sm.called
        )

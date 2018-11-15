import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import smoke_test


@mock.patch(
    "intrahospital_api.management.commands.smoke_test.service.smoke_test"
)
@mock.patch(
    "intrahospital_api.management.commands.smoke_test.logger.info"
)
class SmokeTestTestCase(OpalTestCase):
    def setUp(self):
        super(SmokeTestTestCase, self).setUp()
        self.handle = smoke_test.Command().handle

    def test_batch_appointments_load(self, info, sm):
        self.handle()
        self.assertTrue(
            sm.called
        )
        self.assertEqual(
            info.call_args_list[0][0][0],
            "Starting smoke test"
        )
        self.assertEqual(
            info.call_args_list[1][0][0],
            "Smoke test complete"
        )


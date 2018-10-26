import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import batch_appointments_load

BASE_MOCK_STR = """
intrahospital_api.management.commands.batch_appointments_load.{}
""".strip()


@mock.patch(BASE_MOCK_STR.format("service.batch_load"))
class BatchAppointmentsTestCase(OpalTestCase):
    def setUp(self):
        super(BatchAppointmentsTestCase, self).setUp()
        self.handle = batch_appointments_load.Command().handle

    def test_batch_appointments_load(self, batch_load):
        handle()
        self.assertTrue(
            batch_load.called
        )
import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import load_appointments

SERVICE = "intrahospital_api.services.appointments.service"

@mock.patch(
    SERVICE + "update_future_appointments",
    SERVICE + "update_all_appointments_in_the_last_year",
)
class LoadAppointmentsTestCase(OpalTestCase):
    def setUp(self):
        self.cmd = load_appointments.Command()

    def test_add_appointments(
        self,
        update_all_appointments_in_the_last_year,
        update_future_appointments
    ):

        parser = mock.MagicMock()
        self.cmd.add_arguments(parser)
        parser.add_arguments.assert_called_once_with(
            "---force", action="store_true"
        )

    def test_handle_force(
        self,
        update_all_appointments_in_the_last_year,
        update_future_appointments
    ):
        self.cmd.handle(force=True)
        self.assertTrue(
            update_all_appointments_in_the_last_year.called
        )
        self.assertFalse(
            update_future_appointments.called
        )

    def test_handle_not_force(
        self,
        update_all_appointments_in_the_last_year,
        update_future_appointments
    ):
        self.cmd.handle(force=True)
        self.assertFalse(
            update_all_appointments_in_the_last_year.called
        )
        self.assertTrue(
            update_future_appointments.called




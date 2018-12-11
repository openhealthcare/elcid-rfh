import mock
import datetime
from opal.core.test import OpalTestCase
from intrahospital_api.services.appointments import dev_backend as dev

PACKAGE_STRING = """
intrahospital_api.services.appointments.dev_backend.{}
""".strip()


class DevBackendTestCase(OpalTestCase):
    def setUp(self):
        super(DevBackendTestCase, self).setUp()
        self.backend = dev.Backend()

    @mock.patch(PACKAGE_STRING.format("random.randint"))
    @mock.patch(PACKAGE_STRING.format("datetime"))
    def test_raw_appointements(self, dt, randint):
        now = datetime.datetime.now()
        dt.datetime.now.return_value = now
        dt.timedelta = datetime.timedelta
        randint.return_value = 1
        appointment = self.backend.raw_appointment("111")
        self.assertEqual(
            appointment["Patient_Number"], "111"
        )
        self.assertEqual(
            appointment["Appointment_Start_Datetime"],
            now + datetime.timedelta(1)
        )
        self.assertEqual(
            appointment["Appointment_End_Datetime"],
            now + datetime.timedelta(1) + datetime.timedelta(hours=1)
        )

    def test_raw_appointements_for_hospital_number(self):
        with mock.patch.object(self.backend, "raw_appointment") as ra:
            ra.return_value = "fake appointment"
            result = self.backend.raw_appointments_for_hospital_number("111")
            self.assertEqual(result, ["fake appointment"])
            self.assertEqual(ra.call_count, 1)

    def test_raw_tb_appointments_for_hospital_number(self):
        with mock.patch.object(self.backend, "raw_appointment") as ra:
            ra.return_value = "fake appointment"
            result = self.backend.raw_tb_appointments_for_hospital_number("111")
            self.assertEqual(result, ["fake appointment"])
            self.assertEqual(ra.call_count, 1)

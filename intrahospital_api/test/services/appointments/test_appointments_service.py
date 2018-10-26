import datetime
import mock
import copy
from django.utils import timezone
from opal.core.test import OpalTestCase
from intrahospital_api.services.appointments import service
from opal.models import Patient
from elcid import models as elcid_models
from apps.tb import models as tb_models
from apps.tb.episode_categories import TbEpisode

SERVICE_STR = "intrahospital_api.services.appointments.service.{}"

RESPONSE = {
    'clinic_resource': u'RAL Davis, Dr David TB',
    'end': datetime.datetime(2018, 9, 18, 15, 10),
    'location': u'RAL GROVE CLINIC',
    'start': datetime.datetime(2018, 9, 18, 14, 0),
    'state': u'Confirmed'
}

API_RESPONSE = {
    'clinic_resource': u'RAL Davis, Dr David TB',
    'end': "18/09/2018 15:10:00",
    'start': "18/09/2018 14:10:00",
    'location': u'RAL GROVE CLINIC',
    'state': u'Confirmed'
}


class AbstractServiceTestCase(OpalTestCase):
    def setUp(self):
        super(AbstractServiceTestCase, self).setUp()
        self.patient, _ = self.new_patient_and_episode_please()

    def get_api_response(self, **kwargs):
        response = copy.copy(API_RESPONSE)
        response.update(**kwargs)
        return response

    def get_appointment(self, **kwargs):
        appointment = elcid_models.Appointment(patient=self.patient)
        for k, v in API_RESPONSE.items():
            setattr(appointment, k, v)

        for k, v in kwargs:
            setattr(appointment, k, v)
        appointment.save()
        return appointment


class RefreshPatientTestCase(AbstractServiceTestCase):
    @mock.patch(SERVICE_STR.format("load_patient"))
    def test_refresh_patient(self, load_patient):
        # create an appointment
        self.get_appointment()
        service.refresh_patient(self.patient)
        self.assertFalse(
            self.patient.appointment_st.all().exists()
        )
        load_patient.assert_called_once_with(self.patient)


class LoadPatientTestCase(AbstractServiceTestCase):
    @mock.patch(
        SERVICE_STR.format(
            "service_utils.get_api.tb_appointments_for_hospital_number"
        )
    )
    def test_load_patient(self, tb_for_hn):
        tb_for_hn.return_value = self.get_api_response()
        service.load_patient(self.patient)
        appointment = self.patient.appointments_set.get()
        for i, v in RESPONSE:
            self.assertEqual(
                getattr(appointment, i), v
            )


class HasChangedTestCase(AbstractServiceTestCase):
    def test_has_changed_true(self):
        pass

    def test_has_changed_false(self):
        pass


class SaveAppointmentsTestCase(AbstractServiceTestCase):
    def test_save_appointments_new(self):
        pass

    def test_save_appointments_old(self):
        pass


class GetOrCreateAppointmentsTestCase(AbstractServiceTestCase):
    def test_new_appointment(self):
        pass

    def test_old_appointment(self):
        pass


class LoadPatientsTestCase(AbstractServiceTestCase):
    def test_load_patients(self):
        pass


class IntegrationTestCase(AbstractServiceTestCase):
    def get_api_result(self):
        return dict(

        )
    def test_integration(self):
        pass
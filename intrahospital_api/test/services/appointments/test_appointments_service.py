import datetime
import mock
import copy
from django.utils import timezone
from intrahospital_api.services.appointments import service
from opal.models import Patient
from elcid import models as elcid_models
from apps.tb import models as tb_models
from apps.tb.episode_categories import TbEpisode
from intrahospital_api.test import test_loader


SERVICE_STR = "intrahospital_api.services.appointments.service.{}"

RESPONSE = {
    'clinic_resource': u'RAL Davis, Dr David TB',
    'end': timezone.make_aware(datetime.datetime(2018, 9, 18, 15, 10)),
    'location': u'RAL GROVE CLINIC',
    'start': timezone.make_aware(datetime.datetime(2018, 9, 18, 14, 10)),
    'state': u'Confirmed'
}

API_RESPONSE = {
    'clinic_resource': u'RAL Davis, Dr David TB',
    'end': "18/09/2018 15:10:00",
    'start': "18/09/2018 14:10:00",
    'location': u'RAL GROVE CLINIC',
    'state': u'Confirmed'
}


class AbstractServiceTestCase(test_loader.ApiTestCase):
    def setUp(self):
        super(AbstractServiceTestCase, self).setUp()
        self.patient, episode = self.new_patient_and_episode_please()
        episode.category_name = TbEpisode.display_name
        episode.save()

    def get_api_response(self, **kwargs):
        response = copy.copy(API_RESPONSE)
        response.update(**kwargs)
        return [response]

    def get_appointment(self, **kwargs):
        appointment = elcid_models.Appointment(
            patient=self.patient,
            created_by=self.user,
            created=timezone.now()
        )
        for k, v in RESPONSE.items():
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
            self.patient.appointment_set.all().exists()
        )
        load_patient.assert_called_once_with(self.patient)


class LoadPatientTestCase(AbstractServiceTestCase):
    @mock.patch(
        SERVICE_STR.format(
            "service_utils.get_api"
        )
    )
    def test_load_patient(self, get_api):
        api = get_api.return_value
        api.tb_appointments_for_hospital_number.return_value = self.get_api_response()
        service.load_patient(self.patient)
        appointment = self.patient.appointment_set.get()
        for i, v in RESPONSE.items():
            self.assertEqual(
                getattr(appointment, i), v
            )


class HasChangedTestCase(AbstractServiceTestCase):
    def test_has_changed_true(self):
        appointment = self.get_appointment()
        appointment_dict = self.get_api_response(state="DNA")[0]
        self.assertTrue(
            service.has_changed(
                appointment, appointment_dict
            )
        )

    def test_has_changed_false(self):
        appointment = self.get_appointment()
        appointment_dict = self.get_api_response()[0]
        self.assertFalse(
            service.has_changed(
                appointment, appointment_dict
            )
        )


class SaveAppointmentsTestCase(AbstractServiceTestCase):
    def test_save_appointments_new(self):
        appointment_dicts = self.get_api_response()
        service.save_appointments(self.patient, appointment_dicts)
        appointment = elcid_models.Appointment.objects.first()
        self.assertEqual(appointment.patient, self.patient)

    def test_save_appointments_unchanged_old(self):
        appointment = self.get_appointment()
        appointment.updated = None
        appointment.save()
        appointment_dicts = self.get_api_response()
        service.save_appointments(self.patient, appointment_dicts)

        reloaded_appointment = elcid_models.Appointment.objects.get(
            id=appointment.id
        )
        self.assertIsNone(reloaded_appointment.updated)

    def test_save_appointments_changed_old(self):
        appointment = self.get_appointment()
        appointment.updated = None
        appointment.save()
        appointment_dicts = self.get_api_response(state="DNA")
        service.save_appointments(self.patient, appointment_dicts)
        reloaded_appointment = elcid_models.Appointment.objects.get(
            id=appointment.id
        )
        self.assertIsNotNone(reloaded_appointment.updated)


class GetOrCreateAppointmentsTestCase(AbstractServiceTestCase):
    def test_old_appointment(self):
        appointment_dict = self.get_api_response()[0]
        appointment, created = service.get_or_create_appointment(
            self.patient, appointment_dict
        )
        self.assertEqual(appointment.patient, self.patient)
        self.assertTrue(created)

    def test_new_appointment(self):
        appointment_dict = self.get_api_response()[0]
        self.get_appointment()
        _, created = service.get_or_create_appointment(
            self.patient, appointment_dict
        )
        self.assertFalse(created)


@mock.patch('intrahospital_api.services.appointments.service.load_patient')
class LoadPatientsTestCase(AbstractServiceTestCase):
    def test_load_patient_tb(self, load_patient):
        service.load_patients()
        load_patient.assert_called_once_with(self.patient)

    def test_load_patient_not_tb(self, load_patient):
        self.patient.episode_set.update(
            category_name="Infection Service"
        )
        service.load_patients()
        self.assertFalse(load_patient.called)

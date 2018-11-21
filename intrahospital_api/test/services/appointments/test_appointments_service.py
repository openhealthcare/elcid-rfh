import datetime
import mock
import copy
from django.utils import timezone
from intrahospital_api.services.appointments import service
from opal.models import Patient
from elcid import models as elcid_models
from apps.tb import models as tb_models
from apps.tb.episode_categories import TbEpisode
from intrahospital_api.test.core import ApiTestCase


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


class AbstractServiceTestCase(ApiTestCase):
    def setUp(self):
        super(AbstractServiceTestCase, self).setUp()
        self.patient = self.create_tb_patient()

    def create_tb_patient(self):
        patient, episode = self.new_patient_and_episode_please()
        episode.category_name = TbEpisode.display_name
        episode.save()
        return patient

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
    @mock.patch(SERVICE_STR.format("_load_patient"))
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
            "service_utils.get_backend"
        )
    )
    def test_load_patient(self, get_backend):
        api = get_backend.return_value
        api.tb_appointments_for_hospital_number.return_value = self.get_api_response()
        service._load_patient(self.patient)
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
            service._has_changed(
                appointment, appointment_dict
            )
        )

    def test_has_changed_false(self):
        appointment = self.get_appointment()
        appointment_dict = self.get_api_response()[0]
        self.assertFalse(
            service._has_changed(
                appointment, appointment_dict
            )
        )


class SaveAppointmentsTestCase(AbstractServiceTestCase):
    def test_save_appointments_new(self):
        appointment_dicts = self.get_api_response()
        result = service._save_appointments(self.patient, appointment_dicts)
        appointment = elcid_models.Appointment.objects.first()
        self.assertEqual(appointment.patient, self.patient)
        self.assertTrue(result)

    def test_save_appointments_unchanged_old(self):
        appointment = self.get_appointment()
        appointment.updated = None
        appointment.save()
        appointment_dicts = self.get_api_response()
        result = service._save_appointments(self.patient, appointment_dicts)

        reloaded_appointment = elcid_models.Appointment.objects.get(
            id=appointment.id
        )
        self.assertIsNone(reloaded_appointment.updated)
        self.assertFalse(result)

    def test_save_appointments_changed_old(self):
        appointment = self.get_appointment()
        appointment.updated = None
        appointment.save()
        appointment_dicts = self.get_api_response(state="DNA")
        result = service._save_appointments(self.patient, appointment_dicts)
        reloaded_appointment = elcid_models.Appointment.objects.get(
            id=appointment.id
        )
        self.assertIsNotNone(reloaded_appointment.updated)
        self.assertTrue(result)

    def test_save_multiple_appointments(self):
        appointment_dict_1 = self.get_api_response()[0]
        appointment_dict_2 = self.get_api_response(
            start="19/09/2018 14:10:00",
            end="19/09/2018 15:10:00"
        )[0]
        appointment_dicts = [appointment_dict_1, appointment_dict_2]
        service._save_appointments(self.patient, appointment_dicts)
        appointments = elcid_models.Appointment.objects.all()
        self.assertEqual(appointments.count(), 2)
        self.assertEqual(self.patient.appointment_set.count(), 2)

        self.assertTrue(
            appointments.filter(
                start=timezone.make_aware(
                    datetime.datetime(2018, 9, 18, 14, 10)
                )
            ).exists()
        )

        self.assertTrue(
            appointments.filter(
                start=timezone.make_aware(
                    datetime.datetime(2018, 9, 19, 14, 10)
                )
            ).exists()
        )


class GetOrCreateAppointmentsTestCase(AbstractServiceTestCase):
    def test_old_appointment(self):
        appointment_dict = self.get_api_response()[0]
        appointment, created = service._get_or_create_appointment(
            self.patient, appointment_dict
        )
        self.assertEqual(appointment.patient, self.patient)
        self.assertTrue(created)

    def test_new_appointment(self):
        appointment_dict = self.get_api_response()[0]
        self.get_appointment()
        _, created = service._get_or_create_appointment(
            self.patient, appointment_dict
        )
        self.assertFalse(created)


@mock.patch('intrahospital_api.services.appointments.service._load_patient')
class LoadPatientsTestCase(AbstractServiceTestCase):
    def test_load_patient_tb(self, load_patient):
        load_patient.return_value = True
        result = service._load_patients()
        load_patient.assert_called_once_with(self.patient)
        self.assertEqual(
            result, 1
        )

    def test_load_patient_not_tb(self, load_patient):
        load_patient.return_value = True
        self.patient.episode_set.update(
            category_name="Infection Srvice"
        )
        result = service._load_patients()
        self.assertFalse(load_patient.called)
        self.assertEqual(
            result, 0
        )

    def test_load_patients_multiple(self, load_patient):
        for _ in xrange(3):
            self.create_tb_patient()

        # 4 because another patient is created by the test setup
        load_patient.side_effect = [1, 3, 2, 0]
        result = service._load_patients()
        self.assertEqual(
            result, sum([1, 3, 2, 0])
        )

import mock
import datetime
from django.conf import settings
from django.utils import timezone
from django.test import override_settings
from opal.core.test import OpalTestCase
from opal.core import serialization
from opal import models as opal_models
from lab import models as lab_models
from elcid import models as elcid_models
from intrahospital_api.services.lab_tests import service
from intrahospital_api import models
from intrahospital_api.test.core import ApiTestCase

LAB_TEST_BASE = "intrahospital_api.services.lab_tests.service"


@mock.patch(
    "{}.service_utils.get_backend".format(LAB_TEST_BASE)
)
class LabTestForHospitalNumberTestCase(ApiTestCase):
    def lab_tests_for_hospital_number(self, get_backend):
        api = get_backend.return_value
        api.fetch_for_identifier.return_value = "result"
        result = service.lab_tests_for_hospital_number("111")
        get_backend.assert_called_once_with("lab_tests")
        api.fetch_for_identifier.assert_called_once_with(
            "111"
        )
        self.assertEqual(result, "result")


class GetModelForLabTestTypeTestCase(OpalTestCase):
    def setUp(self):
        super(GetModelForLabTestTypeTestCase, self).setUp()
        self.patient, _ = self.new_patient_and_episode_please()

    def get_lab_test_dict(self, **kwargs):
        lab_test = dict(
            test_name="BLOOD CULTURE",
            external_identifier="1",
        )
        lab_test.update(kwargs)
        return lab_test

    def create_lab_test(self, lab_test_updates, extras_updates):
        if lab_test_updates is None:
            lab_test_updates = {}

        if extras_updates is None:
            extras_updates = {}

        lab_test = lab_models.LabTest.objects.create(
            patient=self.patient, **lab_test_updates
        )
        lab_test.extras = extras_updates
        lab_test.save()
        return lab_test

    def test_blood_culture_found(self):
        lab_test_updates = dict(
            lab_test_type=elcid_models.UpstreamBloodCulture.get_display_name(),
            external_identifier="1"
        )
        extras_updates = dict(test_name="BLOOD CULTURE")
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )
        lab_test_dict = self.get_lab_test_dict()
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertEqual(
            lab_test.id, result.id
        )

    def test_upstream_lab_test_found(self):
        lab_test_updates = dict(
            lab_test_type=elcid_models.UpstreamLabTest.get_display_name(),
            external_identifier="1"
        )
        extras_updates = dict(test_name="LIVER PROFILE")
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )
        lab_test_dict = self.get_lab_test_dict(
            test_name="LIVER PROFILE"
        )
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertEqual(
            lab_test.id, result.id
        )

    def test_upstream_blood_culture_not_found(self):
        lab_test_dict = self.get_lab_test_dict()
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertIsNone(result.id)
        self.assertEqual(
            result.__class__, elcid_models.UpstreamBloodCulture
        )

    def test_upstream_lab_test_not_found(self):
        lab_test_dict = self.get_lab_test_dict(test_name="LIVER PROFILE")
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertIsNone(result.id)
        self.assertEqual(
            result.__class__, elcid_models.UpstreamLabTest
        )

    def test_does_not_return_wrong_model_type_blood_culture(self):
        """
        If we are looking for an Upstream Blood Culture
        with id "1" we should not return an
        Upstream Lab Test
        """
        lab_test_updates = dict(
            lab_test_type=elcid_models.UpstreamBloodCulture.get_display_name(),
            external_identifier="1"
        )
        extras_updates = dict(test_name="BLOOD CULTURE")
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )
        lab_test_dict = self.get_lab_test_dict(test_name="LIVER PROFILE")
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertIsNone(result.id)
        self.assertEqual(
            result.__class__, elcid_models.UpstreamLabTest
        )

    def test_does_not_return_wrong_model_type_lab_test(self):
        """
        If we are looking for an Upstream Blood Culture
        with id "1" we should not return an
        Upstream Lab Test
        """
        lab_test_updates = dict(
            lab_test_type=elcid_models.UpstreamLabTest.get_display_name(),
            external_identifier="1"
        )
        extras_updates = dict(test_name="LIVER PROFILE")
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )
        lab_test_dict = self.get_lab_test_dict(test_name="BLOOD CULTURE")
        result = service.get_model_for_lab_test_type(
            self.patient, lab_test_dict
        )
        self.assertIsNone(result.id)
        self.assertEqual(
            result.__class__, elcid_models.UpstreamBloodCulture
        )

    def test_multiple_tests(self):
        lab_test_updates = dict(
            lab_test_type=elcid_models.UpstreamLabTest.get_display_name(),
            external_identifier="1"
        )
        extras_updates = dict(test_name="LIVER PROFILE")
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )
        lab_test = self.create_lab_test(
            lab_test_updates, extras_updates=extras_updates
        )

        lab_test_dict = self.get_lab_test_dict(
            test_name="LIVER PROFILE"
        )
        with self.assertRaises(ValueError) as ve:
            service.get_model_for_lab_test_type(
                self.patient, lab_test_dict
            )
        self.assertEqual(
            str(ve.exception), "multiple test types found for 1 LIVER PROFILE"
        )


class UpdatePatientsTestCase(ApiTestCase):
    @mock.patch("intrahospital_api.services.lab_tests.service.update_patient")
    def test_multiple_patients_with_the_same_hospital_number(
        self, update_patient
    ):
        patient_1, _ = self.new_patient_and_episode_please()
        patient_2, _ = self.new_patient_and_episode_please()
        patient_1.demographics_set.update(
            hospital_number="111", first_name="Wilma", surname="Flintstone"
        )
        patient_2.demographics_set.update(
            hospital_number="111", first_name="Betty", surname="Rubble"
        )
        service.update_patients(
            opal_models.Patient.objects.filter(
                id__in=[patient_1.id, patient_2.id]
            ),
            datetime.datetime.now()
        )

        call_args_list = update_patient.call_args_list
        called_patients = set([
            call_args_list[0][0][0],
            call_args_list[1][0][0]
        ])

        self.assertEqual(
            called_patients, set([patient_1, patient_2])
        )

    @mock.patch("intrahospital_api.services.lab_tests.service.service_utils")
    @mock.patch("intrahospital_api.services.lab_tests.service.update_patient")
    def test_multiple_patients(
        self, update_patient, service_utils
    ):
        api = service_utils.get_backend.return_value
        api.lab_test_results_since.return_value = {
            "111": ["some_lab_tests"],
            "112": ["some_other_lab_tests"],
        }
        patient_1, _ = self.new_patient_and_episode_please()
        patient_2, _ = self.new_patient_and_episode_please()
        patient_1.demographics_set.update(
            hospital_number="111", first_name="Wilma", surname="Flintstone"
        )
        patient_2.demographics_set.update(
            hospital_number="112", first_name="Betty", surname="Rubble"
        )
        service.update_patients(
            opal_models.Patient.objects.filter(
                id__in=[patient_1.id, patient_2.id]
            ),
            datetime.datetime.now()
        )

        call_args_list = update_patient.call_args_list
        self.assertEqual(
            call_args_list[0], mock.call(patient_1, ['some_lab_tests'])
        )
        self.assertEqual(
            call_args_list[1], mock.call(patient_2, ['some_other_lab_tests'])
        )


@mock.patch('{}.update_patients'.format(LAB_TEST_BASE))
class BatchLoadTestCase(ApiTestCase):
    def test_batch_load(self, update_patients):
        patient, _ = self.new_patient_and_episode_please()
        started = timezone.now() - datetime.timedelta(seconds=20)
        stopped = timezone.now() - datetime.timedelta(seconds=10)
        models.InitialPatientLoad.objects.create(
            started=started,
            stopped=stopped,
            patient=patient,
            state=models.InitialPatientLoad.SUCCESS
        )
        update_patients.return_value = 2
        result = service.lab_test_batch_load()
        call_args = update_patients.call_args
        self.assertEqual(
            call_args[0][0].get(), patient
        )

        self.assertEqual(
            call_args[0][1], started
        )

        self.assertEqual(result, 2)


@mock.patch(
    "intrahospital_api.services.lab_tests.service.update_patient"
)
class RefreshPatientTestCase(OpalTestCase):
    def test_refresh_patient(self, update_patient):
        patient, _ = self.new_patient_and_episode_please()
        patient.labtest_set.create(
            lab_test_type=elcid_models.UpstreamBloodCulture.get_display_name(),
            external_identifier="123",
            extras=dict(
                observations=[dict(
                    observation_value="0.11",
                    last_updated="12/11/2018 07:07:28"
                )]
            )
        )
        patient.labtest_set.create(
            lab_test_type=elcid_models.UpstreamLabTest.get_display_name(),
            external_identifier="123",
            extras=dict(
                observations=[dict(
                    observation_value="0.11",
                    last_updated="12/11/2018 07:07:28"
                )]
            )
        )
        service.refresh_patient(patient)
        self.assertFalse(
            patient.labtest_set.exists()
        )
        update_patient.assert_called_once_with(patient)


@mock.patch("{}.refresh_patient".format(LAB_TEST_BASE))
@mock.patch("{}.load_utils.get_loaded_patients".format(LAB_TEST_BASE))
class RefreshAllTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()

    def test_returns_a_count(
        self, get_loaded_patients, refresh_patient
    ):
        get_loaded_patients.return_value = opal_models.Patient.objects.filter(
            id=self.patient.id
        )
        refresh_patient.return_value = 2
        result = service._refresh_all()

        self.assertEqual(result, 2)
        refresh_patient.assert_called_once_with(self.patient)

    def test_public_method(
        self, get_loaded_patients, refresh_patient
    ):
        get_loaded_patients.return_value = opal_models.Patient.objects.filter(
            id=self.patient.id
        )
        refresh_patient.return_value = 2
        service.refresh_all()
        bpl = models.BatchPatientLoad.objects.get(
            service_name=service.SERVICE_NAME
        )
        self.assertEqual(
            bpl.count, 2
        )
        refresh_patient.assert_called_once_with(self.patient)

class DiffPatientTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(
            hospital_number="111"
        )
        self.max_dt = timezone.make_aware(
            datetime.datetime(
                2018, 12, 10, 11, 8
            )
        )
        future_time = self.max_dt + datetime.timedelta(hours=1)

        self.future_time_str = future_time.strftime(
            settings.DATETIME_INPUT_FORMATS[0]
        )

    def create_lab_test(self, lab_test_number, observations_list):
        return self.patient.labtest_set.create(
            lab_test_type=elcid_models.UpstreamLabTest.get_display_name(),
            external_identifier=lab_test_number,
            extras=dict(observations=observations_list)
        )

    def test_no_diff(self):
        db_results = {
            "111": [
                ("0.11", '12/11/2018 07:07:28')
            ]
        }
        self.create_lab_test("111", [dict(
            observation_value="0.11",
            last_updated="12/11/2018 07:07:28"
        )])
        result = service.diff_patient(
            self.patient, db_results, self.max_dt
        )
        self.assertIsNone(result)

    def test_missing_lab_tests(self):
        db_results = {
            "111": [
                ("0.11", '12/11/2018 07:07:28')
            ]
        }
        result = service.diff_patient(
            self.patient, db_results, self.max_dt
        )
        self.assertEqual(
            result, dict(
                missing_lab_tests=set(["111"]),
                different_observations={},
                additional_lab_tests=set()
            )
        )

    def test_additional_lab_tests(self):
        db_results = {}
        self.create_lab_test("111", [dict(
            observation_value="0.11",
            last_updated="12/11/2018 07:07:28"
        )])
        result = service.diff_patient(
            self.patient, db_results, self.max_dt
        )
        self.assertEqual(
            result, dict(
                missing_lab_tests=set(),
                different_observations={},
                additional_lab_tests=set(["111"])
            )
        )

    def test_additional_observations(self):
        """
        For the moment if we have additional observations
        locally, this is ok
        """
        self.create_lab_test("111", [
            dict(
                observation_value="0.11",
                last_updated="12/11/2018 07:07:28"
            ),
            dict(
                observation_value="0.12",
                last_updated="12/11/2018 08:07:28"
            ),
        ])

        db_results = {
            "111": [
                ("0.11", '12/11/2018 07:07:28')
            ]
        }
        result = service.diff_patient(
            self.patient, db_results, self.max_dt
        )
        self.assertIsNone(result)

    def test_missing_observations(self):
        self.create_lab_test("111", [
            dict(
                observation_value="0.11",
                last_updated="12/11/2018 07:07:28"
            ),
        ])

        db_results = {
            "111": [
                ("0.11", '12/11/2018 07:07:28'),
                ("0.12", '12/11/2018 08:07:28'),
            ]
        }
        result = service.diff_patient(
            self.patient, db_results, self.max_dt
        )
        self.assertEqual(
            result, dict(
                missing_lab_tests=set(),
                different_observations={
                    "111": dict(
                        missing_observations=set([
                            ("0.12", "12/11/2018 08:07:28",),
                        ]),
                    )
                },
                additional_lab_tests=set()
            )
        )

    def test_ignore_our_lab_tests_with_all_obs_over_the_max_dt(self):
        self.create_lab_test("111", [
            dict(
                observation_value="0.11",
                last_updated=self.future_time_str
            ),
        ])
        db_results = {}
        result = service.diff_patient(
            self.patient, db_results, self.max_dt
        )
        self.assertIsNone(result)

    def test_ignore_their_lab_tests_with_all_obs_over_the_max(self):
        db_results = {"111": [
            ("0.11", self.future_time_str,),
        ]}
        result = service.diff_patient(
            self.patient, db_results, self.max_dt
        )
        self.assertIsNone(result)

    def test_ignore_observations_with_some_of_our_obs_over_the_max(self):
        db_results = {
            "111": [
                ("0.11", '12/11/2018 07:07:28')
            ]
        }
        self.create_lab_test("111", [
            dict(
                observation_value="0.11",
                last_updated="12/11/2018 07:07:28"
            ),
            dict(
                observation_value="0.11",
                last_updated=self.future_time_str
            ),
        ])
        result = service.diff_patient(
            self.patient, db_results, self.max_dt
        )
        self.assertIsNone(result)

    def test_ignore_observations_with_some_of_our_obs_over_the_max(self):
        db_results = {
            "111": [
                ("0.11", '12/11/2018 07:07:28'),
                ("0.12", self.future_time_str),
            ]
        }
        self.create_lab_test("111", [
            dict(
                observation_value="0.11",
                last_updated="12/11/2018 07:07:28"
            )
        ])
        result = service.diff_patient(
            self.patient, db_results, self.max_dt
        )
        self.assertIsNone(result)

@mock.patch(
    "intrahospital_api.services.lab_tests.service.load_utils.get_batch_start_time"
)
@mock.patch(
    "intrahospital_api.services.lab_tests.service.service_utils.get_backend"
)
class DiffPatientsTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(
            hospital_number="111"
        )
        self.batch_start_time = timezone.make_aware(
            datetime.datetime(
                2018, 12, 10, 11, 8
            )
        )

    def create_lab_test(self, lab_test_number, observations_list):
        return self.patient.labtest_set.create(
            lab_test_type=elcid_models.UpstreamLabTest.get_display_name(),
            external_identifier=lab_test_number,
            extras=dict(observations=observations_list)
        )

    def test_diff_flow(self, get_backend, get_batch_start_time):
        api = get_backend.return_value
        get_batch_start_time.return_value = self.batch_start_time
        api.get_summaries.return_value = {
            "111": {
                "113": [("0.11", '12/11/2018 07:07:28')]
            }
        }

        self.create_lab_test("112", [dict(
            observation_value="0.12",
            last_updated="13/11/2018 07:07:28"
        )])

        result = service.diff_patients(self.patient)
        self.assertEqual(
            result, {
                "111": dict(
                    missing_lab_tests=set(["113"]),
                    additional_lab_tests=set(["112"]),
                    different_observations={}
                )
            }
        )

    def test_no_diff_flow(self, get_backend, get_batch_start_time):
        api = get_backend.return_value
        get_batch_start_time.return_value = self.batch_start_time
        api.get_summaries.return_value = {
            "111": {
                "113": [("0.11", '12/11/2018 07:07:28')]
            }
        }

        self.create_lab_test("113", [dict(
            observation_value="0.11",
            last_updated="12/11/2018 07:07:28"
        )])

        result = service.diff_patients(self.patient)
        self.assertEqual(
            result, {}
        )


@override_settings(
    DEFAULT_DOMAIN="http://something/",
    DEFAULT_FROM_EMAIL="me@iam.com",
    ADMINS=[("someone", "someone@somewhere.com",)]
)
@mock.patch(
    "intrahospital_api.services.lab_tests.service.django_send_mail"
)
class SendMailTestCase(OpalTestCase):
    def test_send_mail(self, django_send_mail):
        patient_1, _ = self.new_patient_and_episode_please()
        patient_2, _ = self.new_patient_and_episode_please()
        patients = opal_models.Patient.objects.filter(
            id__in=[patient_1.id, patient_2.id]
        )
        service.send_smoke_check_results(patients)
        call_args = django_send_mail.call_args
        self.assertEqual(
            call_args[0][0],
            "The Smoke Check has found 2 issues"
        )
        # the text output of the email
        txt = "http://something/#/patient/{}\nhttp://something/#/patient/{}"
        txt = txt.format(patient_1.id, patient_2.id)

        # the html output of the email
        html = "http://something/#/patient/{}<br />http://something/#/patient/{}"
        html = html.format(patient_1.id, patient_2.id)
        self.assertEqual(
            call_args[0][1], txt
        )
        self.assertEqual(
            call_args[0][2], "me@iam.com"
        )
        self.assertEqual(
            call_args[0][3], ["someone@somewhere.com"]
        )
        self.assertEqual(
            call_args[1], dict(html_message=html)
        )


@mock.patch(
    "intrahospital_api.services.lab_tests.service.send_smoke_check_results"
)
@mock.patch(
    "intrahospital_api.services.lab_tests.service.service_utils.get_backend"
)
class SmokeTestTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.initialpatientload_set.create(
            state=models.InitialPatientLoad.SUCCESS,
            started=timezone.now(),
            stopped=timezone.now()
        )
        self.patient.demographics_set.update(
            hospital_number="111"
        )

    def create_lab_test(self, lab_test_number, observations_list):
        return self.patient.labtest_set.create(
            lab_test_type=elcid_models.UpstreamLabTest.get_display_name(),
            external_identifier=lab_test_number,
            extras=dict(observations=observations_list)
        )

    def test_flow(self, get_backend, send_mail):
        api = get_backend.return_value
        api.get_summaries.return_value = {
            "111": {
                "113": [("0.11", '12/11/2018 07:07:28')]
            }
        }

        self.create_lab_test("112", [dict(
            observation_value="0.12",
            last_updated="13/11/2018 07:07:28"
        )])

        service.smoke_test()
        patient_set = send_mail.call_args[0][0]
        self.assertEqual(
            patient_set.get(), self.patient
        )

    def test_flow_no_issues(self, get_backend, send_mail):
        api = get_backend.return_value
        api.get_summaries.return_value = {
            "111": {
                "113": [("0.11", '12/11/2018 07:07:28')]
            }
        }

        self.create_lab_test("113", [dict(
            observation_value="0.11",
            last_updated="12/11/2018 07:07:28"
        )])

        service.smoke_test()
        self.assertFalse(
            send_mail.called
        )

import mock
import datetime
from intrahospital_api.test.core import ApiTestCase
from intrahospital_api.services.demographics import service
from intrahospital_api.constants import EXTERNAL_SYSTEM


class HaveDemographicsTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name="James",
            surname="Watson",
            sex_ft="Male",
            religion="Christian",
            date_of_birth=datetime.date(1968, 1, 1)
        )
        self.demographics = patient.demographics_set.first()
        super(HaveDemographicsTestCase, self).setUp(*args, **kwargs)

    def test_demographics_have_not_changed(self):
        update_dict = dict(
            first_name="James",
            surname="Watson",
            sex="Male",
            date_of_birth='01/01/1968'
        )
        self.assertFalse(
            service.have_demographics_changed(
                update_dict, self.demographics
            )
        )

    def test_have_changed_fk_or_ft(self):
        update_dict = dict(
            first_name="James",
            surname="Watson",
            sex="not disclosed",
            date_of_birth='01/01/1968'
        )
        self.assertTrue(
            service.have_demographics_changed(
                update_dict, self.demographics
            )
        )

    def test_have_changed_str(self):
        update_dict = dict(
            first_name="Jamey",
            surname="Watson",
            sex="Male",
            date_of_birth='01/01/1968'
        )

        self.assertTrue(
            service.have_demographics_changed(
                update_dict, self.demographics
            )
        )

    def test_have_changed_dt(self):
        update_dict = dict(
            first_name="Jamey",
            surname="Watson",
            sex="Male",
            date_of_birth='02/01/1968'
        )

        self.assertTrue(
            service.have_demographics_changed(
                update_dict, self.demographics
            )
        )


@mock.patch("intrahospital_api.services.demographics.service.service_utils")
class UpdatePatientDemographicsTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(UpdatePatientDemographicsTestCase, self).setUp(*args, **kwargs)
        self.patient, _ = self.new_patient_and_episode_please()
        demographics = self.patient.demographics_set.first()
        demographics.first_name = "Jane"
        demographics.surname = "Bloggs"
        demographics.updated = None
        demographics.save()

    def test_update_patient_demographics_have_changed(self, service_utils):
        mock_backend = mock.MagicMock(name='Mock Backend')
        mock_backend.fetch_for_identifier.return_value = dict(first_name="Janey")
        service_utils.get_backend.return_value = mock_backend
        service_utils.get_user.return_value = self.user
        service.update_patient_demographics(self.patient)
        self.assertEqual(
            self.patient.demographics_set.first().first_name,
            "Janey"
        )

    def test_demographics_passed_in(self, service_utils):
        demographics = service_utils.get_backend.return_value.fetch_for_identifier
        service_utils.get_user.return_value = self.user
        service.update_patient_demographics(
            self.patient, dict(first_name="Janey")
        )
        self.assertEqual(
            self.patient.demographics_set.first().first_name,
            "Janey"
        )
        self.assertFalse(demographics.called)

    def test_no_patient_demographics(self, service_utils):
        # Tests the edge case of where no demographics are found
        demographics = service_utils.get_backend.return_value.fetch_for_identifier
        service_utils.get_user.return_value = self.user
        demographics.return_value = None
        service.update_patient_demographics(self.patient)
        self.assertEqual(
            self.patient.demographics_set.first().first_name, "Jane"
        )
        self.assertEqual(
            self.patient.demographics_set.first().surname, "Bloggs"
        )
        self.assertIsNone(
            self.patient.demographics_set.first().updated
        )

    def test_update_patient_demographics_have_not_changed(self, service_utils):
        demographics = service_utils.get_backend.return_value.fetch_for_identifier
        demographics.return_value = dict(first_name="Jane")
        service.update_patient_demographics(self.patient)
        self.assertIsNone(self.patient.demographics_set.first().updated)


@mock.patch(
    "intrahospital_api.services.demographics.service.logger"
)
@mock.patch(
    "intrahospital_api.services.demographics.service.update_patient_demographics"
)
@mock.patch(
    "intrahospital_api.services.demographics.service.update_external_demographics"
)
@mock.patch(
    "intrahospital_api.services.demographics.service.service_utils.get_backend"
)
class LoadPatientTestCase(ApiTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(
            first_name="Jane",
            hospital_number="111",
            surname="Doe",
            date_of_birth=datetime.date(1995, 12, 1),
            external_system=service.EXTERNAL_SYSTEM
        )
        self.api_response = dict(

            first_name="Jane",
            hospital_number="111",
            surname="Doe",
            date_of_birth="1/12/1995"
        )
        self.api_mock = mock.MagicMock()
        self.api_mock.fetch_for_identifier.return_value = self.api_response

    def replace_existing(
        self,
        get_backend,
        update_external_demographics,
        update_patient_demographics,
        logger
    ):
        self.api_response["first_name"] = "James"
        get_backend.return_value = self.api_mock
        service.load_patient(self.patient)
        update_patient_demographics.assert_called_once_with(
            self.patient, self.api_response
        )
        self.assertFalse(update_external_demographics.called)

    def test_can_reconcile(
        self,
        get_backend,
        update_external_demographics,
        update_patient_demographics,
        logger
    ):
        get_backend.return_value = self.api_mock
        self.api_mock.fetch_for_identifier.return_value = self.api_response
        self.patient.demographics_set.update(
            external_system=None
        )
        service.load_patient(self.patient)
        update_patient_demographics.assert_called_once_with(
            self.patient, self.api_response
        )
        self.assertFalse(update_external_demographics.called)

    def test_cant_reconcile(
        self,
        get_backend,
        update_external_demographics,
        update_patient_demographics,
        logger
    ):
        get_backend.return_value = self.api_mock
        self.api_response["first_name"] = "James"
        self.patient.demographics_set.update(
            external_system=None
        )
        api_dict = dict(
            hospital_number="111",
            first_name="Sally",
            surname="Wilson",
            date_of_birth=datetime.date(2000, 12, 1)
        )
        service.load_patient(self.patient)
        update_external_demographics.assert_called_once_with(
            self.patient, self.api_response
        )
        self.assertFalse(update_patient_demographics.called)

    def test_empty_hospital_number(
        self,
        get_backend,
        update_external_demographics,
        update_patient_demographics,
        logger
    ):
        self.patient.demographics_set.update(
            hospital_number=""
        )
        service.load_patient(self.patient)
        logger.info.assert_called_once_with(
            "unable to find a hospital number for patient id {}".format(
                self.patient.id
            )
        )
        self.assertFalse(get_backend.called)
        self.assertFalse(update_external_demographics.called)
        self.assertFalse(update_patient_demographics.called)

    def test_hospital_number_with_a_space(
        self,
        get_backend,
        update_external_demographics,
        update_patient_demographics,
        logger
    ):
        self.patient.demographics_set.update(
            hospital_number=" "
        )
        service.load_patient(self.patient)
        logger.info.assert_called_once_with(
            "unable to find a hospital number for patient id {}".format(
                self.patient.id
            )
        )
        self.assertFalse(get_backend.called)
        self.assertFalse(update_external_demographics.called)
        self.assertFalse(update_patient_demographics.called)

    def test_unable_to_find_patient(
        self,
        get_backend,
        update_external_demographics,
        update_patient_demographics,
        logger
    ):
        self.api_mock.fetch_for_identifier.return_value = None
        get_backend.return_value = self.api_mock
        service.load_patient(self.patient)
        logger.info.assert_called_once_with(
            "unable to find 111 with the demographic api"
        )
        self.assertFalse(update_external_demographics.called)
        self.assertFalse(update_patient_demographics.called)



@mock.patch("intrahospital_api.services.demographics.service.load_patient")
class SyncDemographicsTestCase(ApiTestCase):
    def test_sync_demographics(self, load_patient):
        patient, _ = self.new_patient_and_episode_please()
        service.load_patients()
        load_patient.assert_called_once_with(patient)


@mock.patch("intrahospital_api.services.demographics.service.service_utils")
class SyncPatientDemographicsTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(SyncPatientDemographicsTestCase, self).setUp(*args, **kwargs)
        self.patient, _ = self.new_patient_and_episode_please()
        self.external_demographics = dict(
            first_name="Wilma",
            surname="Flintstone",
            hospital_number="111",
            date_of_birth=datetime.date(1980, 1, 1),
            sex="Female",
            external_system=EXTERNAL_SYSTEM
        )

    def check_updated(self, demographics):
        self.assertEqual(
            demographics.first_name, "Wilma"
        )
        self.assertEqual(
            demographics.surname, "Flintstone"
        )
        self.assertEqual(
            demographics.date_of_birth, datetime.date(1980, 1, 1)
        )
        self.assertEqual(
            demographics.sex, "Female"
        )
        self.assertEqual(
            demographics.external_system, EXTERNAL_SYSTEM
        )

    def test_external_demographics(self, service_utils):
        dfh = service_utils.get_backend.return_value.fetch_for_identifier
        dfh.return_value = self.external_demographics
        service_utils.get_user.return_value = self.user
        self.patient.demographics_set.update(
            first_name="Betty",
            surname="Flintstone",
            hospital_number="111",
            external_system=EXTERNAL_SYSTEM
        )
        service.load_patient(self.patient)
        self.check_updated(self.patient.demographics_set.first())

    def test_reconcilable_demographics(self, service_utils):
        service_utils.get_user.return_value = self.user
        dfh = service_utils.get_backend.return_value.fetch_for_identifier
        dfh.return_value = self.external_demographics
        self.patient.demographics_set.update(
            first_name="Wilma",
            surname="Flintstone",
            date_of_birth=datetime.date(1980, 1, 1),
            hospital_number="111"
        )
        service.load_patient(self.patient)
        self.check_updated(self.patient.demographics_set.first())

    def test_non_reconcilable_demographics(self, service_utils):
        dfh = service_utils.get_backend.return_value.fetch_for_identifier
        service_utils.get_user.return_value = self.user
        dfh.return_value = self.external_demographics
        self.patient.demographics_set.update(
            first_name="Betty",
            surname="Flintstone",
            date_of_birth=datetime.date(1980, 1, 1),
            hospital_number="111"
        )
        service.load_patient(self.patient)
        demographics = self.patient.demographics_set.first()
        self.assertEqual(
            demographics.first_name, "Betty",
        )
        self.assertEqual(
            demographics.surname, "Flintstone"
        )
        self.assertEqual(
            demographics.date_of_birth, datetime.date(1980, 1, 1)
        )
        self.assertEqual(
            demographics.hospital_number, "111"
        )
        external_demographics = self.patient.externaldemographics_set.get()

        self.assertEqual(
            external_demographics.first_name, "Wilma"
        )
        self.assertEqual(
            external_demographics.surname, "Flintstone"
        )
        self.assertEqual(
            external_demographics.date_of_birth, datetime.date(1980, 1, 1)
        )
        self.assertEqual(
            external_demographics.sex, "Female"
        )

import mock
import datetime
from intrahospital_api.test.test_loader import ApiTestCase
from intrahospital_api.services.demographics import service
from intrahospital_api.constants import EXTERNAL_SYSTEM


class HaveDemographicsTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name="James",
            surname="Watson",
            sex_ft="Male",
            religion="Christian"
        )
        self.demographics = patient.demographics_set.first()
        super(HaveDemographicsTestCase, self).setUp(*args, **kwargs)

    def test_demographics_have_not_changed(self):
        update_dict = dict(
            first_name="James",
            surname="Watson",
            sex="Male"
        )
        self.assertFalse(
            service.have_demographics_changed(
                update_dict, self.demographics
            )
        )

    def test_need_to_service_fk_or_ft(self):
        update_dict = dict(
            first_name="James",
            surname="Watson",
            sex="not disclosed"
        )
        self.assertTrue(
            service.have_demographics_changed(
                update_dict, self.demographics
            )
        )

    def test_need_to_service_str(self):
        update_dict = dict(
            first_name="Jamey",
            surname="Watson",
            sex="Male"
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
        demographics = service_utils.get_api.return_value.demographics_for_hospital_number
        service_utils.get_user.return_value = self.user
        demographics.return_value = dict(first_name="Janey")
        service.update_patient_demographics(self.patient)
        self.assertEqual(
            self.patient.demographics_set.first().first_name,
            "Janey"
        )

    def test_demographics_passed_in(self, service_utils):
        demographics = service_utils.get_api.return_value.demographics_for_hospital_number
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
        demographics = service_utils.get_api.return_value.demographics_for_hospital_number
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
        demographics = service_utils.get_api.return_value.demographics_for_hospital_number
        demographics.return_value = dict(first_name="Jane")
        service.update_patient_demographics(self.patient)
        self.assertIsNone(self.patient.demographics_set.first().updated)


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
        dfh = service_utils.get_api.return_value.demographics_for_hospital_number
        dfh.return_value = self.external_demographics
        service_utils.get_user.return_value = self.user
        self.patient.demographics_set.update(
            first_name="Betty",
            surname="Flintstone",
            external_system=EXTERNAL_SYSTEM
        )
        service.load_patient(self.patient)
        self.check_updated(self.patient.demographics_set.first())

    def test_reconcilable_demographics(self, service_utils):
        service_utils.get_user.return_value = self.user
        dfh = service_utils.get_api.return_value.demographics_for_hospital_number
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
        dfh = service_utils.get_api.return_value.demographics_for_hospital_number
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

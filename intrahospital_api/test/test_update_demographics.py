from unittest import mock
import datetime
from intrahospital_api.test.test_loader import ApiTestCase
from intrahospital_api import update_demographics
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
            update_demographics.have_demographics_changed(
                update_dict, self.demographics
            )
        )

    def test_need_to_update_demographics_fk_or_ft(self):
        update_dict = dict(
            first_name="James",
            surname="Watson",
            sex="not disclosed"
        )
        self.assertTrue(
            update_demographics.have_demographics_changed(
                update_dict, self.demographics
            )
        )

    def test_need_to_update_demographics_str(self):
        update_dict = dict(
            first_name="Jamey",
            surname="Watson",
            sex="Male"
        )

        self.assertTrue(
            update_demographics.have_demographics_changed(
                update_dict, self.demographics
            )
        )


@mock.patch(
    "intrahospital_api.update_demographics.reconcile_patient_demographics"
)
class ReconcileDemographicsTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(ReconcileDemographicsTestCase, self).setUp(*args, **kwargs)

        # this is the patient that will be covered
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(
            external_system="blah",
            hospital_number="123",
            updated=None
        )
        # we should not see this patient as they have an exernal system on
        # their demographics
        patient_2, _ = self.new_patient_and_episode_please()
        patient_2.demographics_set.update(
            external_system=EXTERNAL_SYSTEM,
            hospital_number="234",
        )

    def test_reconcile_all_demographics(self, reconcile_patient_demographics):
        update_demographics.reconcile_all_demographics()
        reconcile_patient_demographics.assert_called_once_with(self.patient)


@mock.patch.object(update_demographics.logger, 'info')
@mock.patch.object(update_demographics.api, 'demographics')
class ReconcilePatientDemographicsTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(ReconcilePatientDemographicsTestCase, self).setUp(
            *args, **kwargs
        )

        # this is the patient that will be covered
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(
            external_system="blah",
            hospital_number="123",
            updated=None
        )

    def test_not_reconcilable_patient_demographics(self, demographics, info):
        demographics.return_value = dict(
            first_name="Jane",
            surname="Doe",
            date_of_birth="12/10/2000",
            external_system=EXTERNAL_SYSTEM,
            hospital_number="123"
        )
        update_demographics.reconcile_patient_demographics(self.patient)
        demographics.assert_called_once_with("123")
        self.assertFalse(info.called)
        self.assertEqual(
            self.patient.externaldemographics_set.first().first_name,
            "Jane"
        )
        self.assertIsNotNone(
            self.patient.externaldemographics_set.first().updated
        )

    def test_reconcilable_patient_demographics(self, demographics, info):
        demographics.return_value = dict(
            first_name="Jane",
            surname="Doe",
            date_of_birth=None,
            external_system="blah",
            hospital_number="123",
            sex="Male"
        )
        patient, _ = self.new_patient_and_episode_please()
        demographics = patient.demographics_set.first()
        demographics.first_name = "Jane"
        demographics.surname = "Doe"
        demographics.hospital_number = "123"
        demographics.date_of_birth = None
        demographics.save()
        update_demographics.reconcile_patient_demographics(patient)
        self.assertFalse(info.called)
        self.assertEqual(
            patient.demographics_set.first().first_name,
            "Jane"
        )

        self.assertEqual(
            patient.demographics_set.first().sex,
            "Male"
        )

    def test_with_external_demographics_when_none(self, demographics, info):
        demographics.return_value = None
        update_demographics.reconcile_patient_demographics(self.patient)
        self.assertIsNone(
            self.patient.externaldemographics_set.first().updated
        )
        info.assert_called_once_with("unable to find 123")

    def test_handle_date_of_birth(self, demographics, info):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            external_system="test",
        )
        demographics.return_value = dict(
            external_system="Test",
            date_of_birth="27/10/2000",
            first_name="Jane",
            surname="Doe",
            hospital_number="123"
        )
        update_demographics.reconcile_patient_demographics(patient)
        external_demographics = patient.externaldemographics_set.last()
        self.assertEqual(
            external_demographics.date_of_birth,
            datetime.date(2000, 10, 27)
        )


@mock.patch.object(update_demographics.api, 'demographics')
class UpdatePatientDemographicsTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(UpdatePatientDemographicsTestCase, self).setUp(*args, **kwargs)
        self.patient, _ = self.new_patient_and_episode_please()
        demographics = self.patient.demographics_set.first()
        demographics.first_name = "Jane"
        demographics.surname = "Bloggs"
        demographics.updated = None
        demographics.save()

    def test_update_patient_demographics_have_changed(self, demographics):
        demographics.return_value = dict(first_name="Janey")
        update_demographics.update_patient_demographics(self.patient)
        self.assertEqual(
            self.patient.demographics_set.first().first_name,
            "Janey"
        )

    def test_demographics_passed_in(self, demographics):
        update_demographics.update_patient_demographics(
            self.patient, dict(first_name="Janey")
        )
        self.assertEqual(
            self.patient.demographics_set.first().first_name,
            "Janey"
        )
        self.assertFalse(demographics.called)

    def test_no_patient_demographics(self, demographics):
        # Tests the edge case of where no demographics are found
        demographics.return_value = None
        update_demographics.update_patient_demographics(self.patient)
        self.assertEqual(
            self.patient.demographics_set.first().first_name, "Jane"
        )
        self.assertEqual(
            self.patient.demographics_set.first().surname, "Bloggs"
        )
        self.assertIsNone(
            self.patient.demographics_set.first().updated
        )

    def test_update_patient_demographics_have_not_changed(self, demographics):
        demographics.return_value = dict(first_name="Jane")
        update_demographics.update_patient_demographics(self.patient)
        self.assertIsNone(self.patient.demographics_set.first().updated)

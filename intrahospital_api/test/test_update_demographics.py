from unittest import mock
import datetime
from opal.core.test import OpalTestCase
from django.utils import timezone
from elcid.models import Demographics
from intrahospital_api.test.test_loader import ApiTestCase
from intrahospital_api import update_demographics
from intrahospital_api.constants import EXTERNAL_SYSTEM


class UpdateIfChangedTestCase(OpalTestCase):
    def setUp(self):
        patient, _ = self.new_patient_and_episode_please()
        self.demographics = patient.demographics()
        self.update_dict = {}

    def test_update_date(self):
        self.update_dict["date_of_birth"] = datetime.date(
            2001, 1, 1
        )
        self.demographics.date_of_birth = datetime.date(
            2001, 1, 2
        )
        self.demographics.save()
        update_demographics.update_if_changed(
            self.demographics,
            self.update_dict
        )
        demo = Demographics.objects.get()
        self.assertEqual(
            demo.date_of_birth, self.update_dict["date_of_birth"]
        )
        self.assertTrue(
            bool(demo.updated)
        )

    def test_not_update_date(self):
        self.update_dict["date_of_birth"] = datetime.date(
            2001, 1, 1
        )
        self.demographics.date_of_birth = datetime.date(
            2001, 1, 1
        )
        self.demographics.save()
        update_demographics.update_if_changed(
            self.demographics,
            self.update_dict
        )
        demo = Demographics.objects.get()
        self.assertEqual(
            demo.date_of_birth, self.update_dict["date_of_birth"]
        )
        self.assertFalse(
            bool(demo.updated)
        )

    def test_update_fk_or_ft(self):
        self.update_dict["title"] = "M"
        update_demographics.update_if_changed(
            self.demographics,
            self.update_dict
        )
        demo = Demographics.objects.get()
        self.assertEqual(
            demo.title, "M"
        )

    def test_update_string(self):
        self.update_dict["first_name"] = "sandra"
        update_demographics.update_if_changed(
            self.demographics,
            self.update_dict
        )
        demo = Demographics.objects.get()
        self.assertEqual(
            demo.first_name, "sandra"
        )

    def test_not_update_string_on_case_difference(self):
        self.update_dict["first_name"] = "Sandra"
        self.demographics.first_name = "sandra"
        self.demographics.save()
        update_demographics.update_if_changed(
            self.demographics,
            self.update_dict
        )
        demo = Demographics.objects.get()
        self.assertEqual(
            demo.first_name, "sandra"
        )
        self.assertFalse(
            bool(demo.updated)
        )

    def test_not_update_none_empty_string(self):
        self.update_dict["nhs_number"] = ""
        update_demographics.update_if_changed(
            self.demographics,
            self.update_dict
        )
        demo = Demographics.objects.get()
        self.assertIsNone(demo.nhs_number)


class HasMasterFileTimestampChangedTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        self.patient, _ = self.new_patient_and_episode_please()
        self.meta = self.patient.masterfilemeta_set.create()
        self.upstream_meta = {}
        self.upstream_patient_information = {
            self.meta.__class__.get_api_name(): self.upstream_meta
        }
        super().setUp(*args, **kwargs)

    def test_true(self):
        self.meta.insert_date = timezone.make_aware(datetime.datetime(
            2019, 1, 1
        ))
        self.meta.save()
        self.upstream_meta["last_updated"] = timezone.make_aware(datetime.datetime(
            2019, 1, 2
        ))
        self.assertTrue(
            update_demographics.has_master_file_timestamp_changed(
                self.patient, self.upstream_patient_information
            )
        )

    def test_false(self):
        self.meta.insert_date = timezone.make_aware(datetime.datetime(
            2019, 1, 3
        ))
        self.meta.save()
        self.upstream_meta["last_updated"] = timezone.make_aware(datetime.datetime(
            2019, 1, 2
        ))
        self.assertFalse(
            update_demographics.has_master_file_timestamp_changed(
                self.patient, self.upstream_patient_information
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


@mock.patch.object(update_demographics.api, 'patient_masterfile')
class UpdatePatientDemographicsTestCase(ApiTestCase):
    def setUp(self, *args, **kwargs):
        super(UpdatePatientDemographicsTestCase, self).setUp(*args, **kwargs)
        self.patient, _ = self.new_patient_and_episode_please()
        demographics = self.patient.demographics_set.first()
        demographics.first_name = "Jane"
        demographics.surname = "Bloggs"
        demographics.hospital_number = "111"
        demographics.updated = None
        demographics.save()

    def test_update_patient_information_have_changed(self, patient_masterfile):
        updated = timezone.make_aware(datetime.datetime(2020, 1, 1))
        upstream = timezone.make_aware(datetime.datetime(2020, 1, 2))
        patient_masterfile.return_value = dict(
            demographics=dict(
                first_name="Janey",
                hospital_number="111"
            ),
            gp_details={},
            master_file_meta={"last_updated": upstream},
            next_of_kin_details={},
            contact_information={}
        )
        self.patient.masterfilemeta_set.update(last_updated=updated)
        update_demographics.update_patient_information(self.patient)
        self.assertEqual(
            self.patient.demographics_set.first().first_name,
            "Janey"
        )

    def test_no_patient_demographics(self, patient_masterfile):
        # Tests the edge case of where no demographics are found
        patient_masterfile.return_value = None
        update_demographics.update_patient_information(self.patient)
        self.assertEqual(
            self.patient.demographics_set.first().first_name, "Jane"
        )
        self.assertEqual(
            self.patient.demographics_set.first().surname, "Bloggs"
        )
        self.assertIsNone(
            self.patient.demographics_set.first().updated
        )

    def test_update_patient_information_have_not_changed(self, patient_masterfile):
        updated = timezone.make_aware(datetime.datetime(2020, 1, 1))
        patient_masterfile.return_value = dict(
            demographics=dict(first_name="Janey"),
            gp_details={},
            master_file_meta={"last_updated": updated},
            next_of_kin_details={},
            contact_information={}
        )
        self.patient.masterfilemeta_set.create(last_updated=updated)
        update_demographics.update_patient_information(self.patient)
        self.assertIsNone(self.patient.demographics_set.first().updated)

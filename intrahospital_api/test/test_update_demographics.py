from unittest import mock
import datetime
import copy
from opal.core.test import OpalTestCase
from opal.models import Patient
from django.utils import timezone
from elcid.models import Demographics, GPDetails
from intrahospital_api.test.test_loader import ApiTestCase
from intrahospital_api import update_demographics
from intrahospital_api.constants import EXTERNAL_SYSTEM


class UpdateIfChangedTestCase(OpalTestCase):
    def setUp(self):
        patient, _ = self.new_patient_and_episode_please()
        # Initialise the user
        self.user
        self.demographics = patient.demographics()
        self.gp_details = patient.gpdetails_set.get()
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

    def test_not_update_string_on_white_space(self):
        self.update_dict["first_name"] = "Sandra "
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

    def test_boolean_changed(self):
        self.demographics.death_indicator = False
        self.update_dict["death_indicator"] = True
        update_demographics.update_if_changed(
            self.demographics,
            self.update_dict
        )
        demo = Demographics.objects.get()
        self.assertTrue(demo.death_indicator)
        self.assertTrue(bool(demo.updated))

    def test_boolean_not_changed(self):
        self.demographics.death_indicator = False
        self.update_dict["death_indicator"] = False
        update_demographics.update_if_changed(
            self.demographics,
            self.update_dict
        )
        demo = Demographics.objects.get()
        self.assertFalse(demo.death_indicator)
        self.assertFalse(bool(demo.updated))

    def test_integer_changed(self):
        self.gp_details.crs_gp_masterfile_id = 111
        self.gp_details.save()
        self.update_dict["crs_gp_masterfile_id"] = 222
        update_demographics.update_if_changed(
            self.gp_details,
            self.update_dict
        )
        gp_details = GPDetails.objects.get()
        self.assertEquals(gp_details.crs_gp_masterfile_id, 222)
        self.assertTrue(bool(gp_details.updated))

    def test_integer_not_changed(self):
        self.gp_details.crs_gp_masterfile_id = 111
        self.gp_details.save()
        self.update_dict["crs_gp_masterfile_id"] = 111
        update_demographics.update_if_changed(
            self.gp_details,
            self.update_dict
        )
        gp_details = GPDetails.objects.get()
        self.assertEquals(gp_details.crs_gp_masterfile_id, 111)
        self.assertFalse(bool(gp_details.updated))


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


class GetMRNAndDateFromMergeCommentTestCase(OpalTestCase):
    def test_no_result(self):
        test_comment = "GP Practice Reset for Dr Madeup GP Practice Reset for Dr Madeup"
        result = update_demographics.get_mrn_and_date_from_merge_comment(
            test_comment
        )
        self.assertEqual(len(result), 0)

    def test_single_result(self):
        test_comment = "Merged with MRN 123456 on Dec  2 2015  9:55AM"
        result = update_demographics.get_mrn_and_date_from_merge_comment(
            test_comment
        )
        self.assertEqual(len(result), 1)
        mrn, merge_dt = result[0]
        self.assertEqual(mrn, "123456")
        self.assertEqual(
            merge_dt,
            timezone.make_aware(
                datetime.datetime(2015, 12, 2, 9, 55)
            )
        )

    def test_messy_result(self):
        """
        Sometimes the comment is prefixed with MIGRATED Data
        """
        test_comment = "MIGRATED DATA Merged with MRN 123456 on Mar  2 2022  2:56PM"
        result = update_demographics.get_mrn_and_date_from_merge_comment(
            test_comment
        )
        self.assertEqual(len(result), 1)
        mrn, merge_dt = result[0]
        self.assertEqual(mrn, "123456")
        self.assertEqual(
            merge_dt,
            timezone.make_aware(
                datetime.datetime(2022, 3, 2, 14, 56)
            )
        )

    def test_ignores_other_information(self):
        """
        Sometimes the comment has other data
        """
        test_comment = " ".join(
            [
                "MIGRATED DATA - GP PRACTICE ADDED",
                "Merged with MRN 123456 on Mar  2 2022  2:57PM"
            ]
        )
        result = update_demographics.get_mrn_and_date_from_merge_comment(
            test_comment
        )
        self.assertEqual(len(result), 1)
        mrn, merge_dt = result[0]
        self.assertEqual(mrn, "123456")
        self.assertEqual(
            merge_dt,
            timezone.make_aware(
                datetime.datetime(2022, 3, 2, 14, 57)
            )
        )

    def test_multiple_results(self):
        test_comment = "Merged with MRN 123456 on Dec  5 2016  3:49PM Merged with MRN 789 on Mar  2 2022  2:56PM"
        result = update_demographics.get_mrn_and_date_from_merge_comment(
            test_comment
        )
        self.assertEqual(len(result), 2)
        mrn, merge_dt = result[0]
        self.assertEqual(mrn, "789")
        self.assertEqual(
            merge_dt,
            timezone.make_aware(
                datetime.datetime(2022, 3, 2, 14, 56)
            )
        )
        mrn, merge_dt = result[1]
        self.assertEqual(mrn, "123456")
        self.assertEqual(
            merge_dt,
            timezone.make_aware(
                datetime.datetime(2016, 12, 5, 15, 49)
            )
        )

class MRNInElcidTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()

    def test_in_demographics(self):
        self.patient.demographics_set.update(hospital_number="123")
        self.assertTrue(update_demographics.mrn_in_elcid("123"))

    def test_in_merged_mrn(self):
        self.patient.mergedmrn_set.create(mrn="123")
        self.assertTrue(update_demographics.mrn_in_elcid("123"))

    def test_in_neither(self):
        self.assertFalse(update_demographics.mrn_in_elcid("123"))


@mock.patch("intrahospital_api.update_demographics.get_mrn_to_upstream_merge_data")
@mock.patch("intrahospital_api.update_demographics.loader.get_or_create_patient")
@mock.patch("intrahospital_api.update_demographics.loader.load_patient")
@mock.patch("intrahospital_api.update_demographics.merge_patient.merge_patient")
class CheckAndHandleUpstreamMergesForMRNsTestCase(OpalTestCase):
    def test_handles_an_inactive_mrn(self, merge_patient, load_patient, get_or_create_patient, get_mrn_to_upstream_merge_data):
        """
        We have a patient with an MRN that has become inactive.

        We should create a new patient with the active MRN and MergedMRN
        with the inactive MRN.
        """
        merge_patient.side_effect = lambda old_patient, new_patient: old_patient.delete()
        get_mrn_to_upstream_merge_data.return_value = {
            "123": {
                "ACTIVE_INACTIVE": "INACTIVE",
                "MERGED": "Y",
                "MRN": "123",
                "MERGE_COMMENTS": "Merged with MRN 234 on Oct 20 2014  4:44PM",
            },
            "234": {
                "ACTIVE_INACTIVE": "ACTIVE",
                "MERGED": "Y",
                "MRN": "234",
                "MERGE_COMMENTS": "Merged with MRN 123 on Oct 20 2014  4:44PM",
            },
        }
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(hospital_number='123')
        def create_patient(*args, **kwargs):
            patient = Patient.objects.create()
            patient.demographics_set.update(hospital_number="234")
            return patient, True
        get_or_create_patient.side_effect = create_patient
        update_demographics.check_and_handle_upstream_merges_for_mrns(["234"])
        patient = Patient.objects.get()
        self.assertEqual(
            patient.demographics().hospital_number, "234"
        )
        merged_mrn = patient.mergedmrn_set.get()
        self.assertEqual(
            merged_mrn.mrn, "123"
        )


    def test_handles_an_active_mrn(self, merge_patient, load_patient, get_or_create_patient, get_mrn_to_upstream_merge_data):
        """
        Locally we have a patient with an active MRN of 123
        Upstream says 123 has an inactive MRN of 234

        We should add a MergedMRN of 234, we should not call merge patient
        """
        get_mrn_to_upstream_merge_data.return_value = {
            "123": {
                "ACTIVE_INACTIVE": "ACTIVE",
                "MERGED": "Y",
                "MRN": "123",
                "MERGE_COMMENTS": "Merged with MRN 234 on Oct 20 2014  4:44PM",
            },
            "234": {
                "ACTIVE_INACTIVE": "INACTIVE",
                "MERGED": "Y",
                "MRN": "234",
                "MERGE_COMMENTS": "Merged with MRN 123 on Oct 20 2014  4:44PM",
            },
        }
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(hospital_number='123')
        update_demographics.check_and_handle_upstream_merges_for_mrns(["234"])
        patient = Patient.objects.get()
        self.assertEqual(
            patient.demographics().hospital_number, "123"
        )
        self.assertFalse(
            get_or_create_patient.called
        )
        merged_mrn = patient.mergedmrn_set.get()
        self.assertEqual(
            merged_mrn.mrn, "234"
        )
        # There is no reason to call merge patient, we are just
        # creating a new MergedMRN
        self.assertFalse(merge_patient.called)

        # Make sure we reload the patient so they have the data including
        # the new merged MRN
        load_patient.assert_called_once_with(patient)

    def test_upstream_merge_between_two_previously_active_mrns(self, merge_patient, load_patient, get_or_create_patient, get_mrn_to_upstream_merge_data):
        """
        Locally we have 2 patients with MRNS 123, 234
        Upstream 123 is merged into 234

        We should merge and delete 123 and add a MergedMRN of 123
        """
        merge_patient.side_effect = lambda old_patient, new_patient: old_patient.delete()
        get_mrn_to_upstream_merge_data.return_value = {
            "123": {
                "ACTIVE_INACTIVE": "INACTIVE",
                "MERGED": "Y",
                "MRN": "123",
                "MERGE_COMMENTS": "Merged with MRN 234 on Oct 20 2014  4:44PM",
            },
            "234": {
                "ACTIVE_INACTIVE": "ACTIVE",
                "MERGED": "Y",
                "MRN": "234",
                "MERGE_COMMENTS": "Merged with MRN 123 on Oct 20 2014  4:44PM",
            },
        }
        patient_1, _ = self.new_patient_and_episode_please()
        patient_1.demographics_set.update(hospital_number='123')
        patient_2, _ = self.new_patient_and_episode_please()
        patient_2.demographics_set.update(hospital_number='234')
        update_demographics.check_and_handle_upstream_merges_for_mrns(["234"])
        reloaded_patient = Patient.objects.get()

        # patient 1 should be deleted and merged intol 2
        self.assertEqual(
            reloaded_patient.id, patient_2.id
        )
        self.assertEqual(
            reloaded_patient.demographics().hospital_number, "234"
        )
        merged_mrn = reloaded_patient.mergedmrn_set.get()
        self.assertEqual(
            merged_mrn.mrn, "123"
        )

    def test_handles_new_inactive_mrns(self, merge_patient, load_patient, get_or_create_patient, get_mrn_to_upstream_merge_data):
        """
        Locally have Patient with MRN 123 and an inactive MRN of 234
        Upstream, 234 and 345 have been merged with 123

        We should create a new merged MRN and not delete the existing Merged MRN MRN.
        We should not call merge_patient
        """
        get_mrn_to_upstream_merge_data.return_value = {
            "123": {
                "ACTIVE_INACTIVE": "ACTIVE",
                "MERGED": "Y",
                "MRN": "123",
                "MERGE_COMMENTS": " ".join([
                    "Merged with MRN 234 on Oct 20 2014  4:44PM",
                    "Merged with MRN 345 on Oct 21 2014  5:44PM",
                ])
            },
            "234": {
                "ACTIVE_INACTIVE": "INACTIVE",
                "MERGED": "Y",
                "MRN": "234",
                "MERGE_COMMENTS": "Merged with MRN 123 on Oct 20 2014  4:44PM",
            },
            "345": {
                "ACTIVE_INACTIVE": "INACTIVE",
                "MERGED": "Y",
                "MRN": "345",
                "MERGE_COMMENTS": "Merged with MRN 123 on Oct 20 2014  5:44PM",
            },
        }
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(hospital_number='123')
        before = timezone.now() - datetime.timedelta(1)
        patient.mergedmrn_set.create(
            mrn="234",
            our_merge_datetime=before,
            merge_comments="Merged with MRN 123 on Oct 20 2014  4:44PM"
        )
        update_demographics.check_and_handle_upstream_merges_for_mrns(["345"])
        patient = Patient.objects.get()
        self.assertEqual(
            patient.demographics().hospital_number, "123"
        )
        self.assertFalse(get_or_create_patient.called)
        # Make sure that we haven't deleted the old one
        self.assertTrue(
            patient.mergedmrn_set.filter(
                mrn="234", our_merge_datetime=before, merge_comments="Merged with MRN 123 on Oct 20 2014  4:44PM"
            ).exists()
        )

        # Make sure wehave created a new one
        self.assertTrue(
            patient.mergedmrn_set.filter(
                mrn="345", merge_comments="Merged with MRN 123 on Oct 20 2014  5:44PM"
            ).exists()
        )
        # There is no reason to call merge patient, we are just
        # creating a new MergedMRN
        self.assertFalse(merge_patient.called)

        # Make sure we reload the patient so they have the data including
        # the new merged MRN
        load_patient.assert_called_once_with(patient)

    def test_does_not_reload_already_merged_patients(self, merge_patient, load_patient, get_or_create_patient, get_mrn_to_upstream_merge_data):
        """
        Locally we have patient with MRN 123 and a merged MRN of 234
        Upstream has 234 as an iactive MRN merged into MRN 123

        We should not change anything.
        We should not reload the patient or create any new MergedMRN objects.
        """
        get_mrn_to_upstream_merge_data.return_value = {
            "123": {
                "ACTIVE_INACTIVE": "ACTIVE",
                "MERGED": "Y",
                "MRN": "123",
                "MERGE_COMMENTS": " ".join([
                    "Merged with MRN 234 on Oct 20 2014  4:44PM",
                ])
            },
            "234": {
                "ACTIVE_INACTIVE": "INACTIVE",
                "MERGED": "Y",
                "MRN": "234",
                "MERGE_COMMENTS": "Merged with MRN 123 on Oct 20 2014  4:44PM",
            },
        }
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(hospital_number='123')
        before = timezone.now() - datetime.timedelta(1)
        patient.mergedmrn_set.create(
            mrn="234",
            our_merge_datetime=before,
            merge_comments="Merged with MRN 123 on Oct 20 2014  4:44PM"
        )
        update_demographics.check_and_handle_upstream_merges_for_mrns(["123"])
        self.assertEqual(patient.mergedmrn_set.get().mrn, "234")
        self.assertFalse(load_patient.called)
        self.assertFalse(merge_patient.called)

    @mock.patch("intrahospital_api.update_demographics.send_email")
    def test_sends_an_email_when_threshold_is_breached(self, send_email, merge_patient, load_patient, get_or_create_patient, get_mrn_to_upstream_merge_data):
        """
        Locally we have a patient with an active MRN of 123
        Upstream says 123 has an inactive MRN of MERGED_MRN_COUNT_EMAIL_THRESHOLD + 1
        inactive MRNs

        We should create the merged MRNS but send an email first
        """
        upstream_data = {
            "123": {
                "ACTIVE_INACTIVE": "ACTIVE",
                "MERGED": "Y",
                "MRN": "123",
                "MERGE_COMMENTS": "",
            },
        }
        for i in range(update_demographics.MERGED_MRN_COUNT_EMAIL_THRESHOLD + 1):
            upstream_inactive_mrn = str(124 + i)
            upstream_data.update({
                upstream_inactive_mrn: {
                    "ACTIVE_INACTIVE": "INACTIVE",
                    "MERGED": "Y",
                    "MRN": upstream_inactive_mrn,
                    "MERGE_COMMENTS": "Merged with MRN 123 on Oct 20 2014  4:44PM",
                }
            })
            upstream_data["123"]["MERGE_COMMENTS"] += f" Merged with MRN {upstream_inactive_mrn} on Oct 20 2014  4:44PM"
        get_mrn_to_upstream_merge_data.return_value = upstream_data
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(hospital_number='123')
        update_demographics.check_and_handle_upstream_merges_for_mrns(["123"])
        patient = Patient.objects.get()
        self.assertEqual(
            patient.demographics().hospital_number, "123"
        )
        self.assertFalse(
            get_or_create_patient.called
        )
        self.assertEqual(
            patient.mergedmrn_set.count(), update_demographics.MERGED_MRN_COUNT_EMAIL_THRESHOLD + 1
        )
        # Make sure we reload the patient so they have the data including
        # the new merged MRN
        load_patient.assert_called_once_with(patient)
        call_args_list = send_email.call_args_list
        self.assertEqual(len(call_args_list), 1)
        self.assertEqual(call_args_list[0][0][0], "We are creating 301 mergedMRNs")
        self.assertEqual(call_args_list[0][0][1], "\n".join([
            "We are creating 301 mergedMRNs",
            "this breaches the threshold of 300",
            "please log in and check this is valid"
        ]))


class GetActiveMrnAndMergedMrnDataTestCase(OpalTestCase):
    BASIC_MAPPING = {
        "123": {
            "MERGE_COMMENTS": "Merged with MRN 234 on Oct 20 2014  4:44PM",
            "ACTIVE_INACTIVE": "INACTIVE",
            "MERGED": "Y"
        },
        "234": {
            "MERGE_COMMENTS": "Merged with MRN 123 on Oct 21 2014  4:44PM",
            "ACTIVE_INACTIVE": "ACTIVE",
            "MERGED": "Y"
        }

    }

    COMPLEX_MAPPING = {
        "345": {
            "MERGE_COMMENTS": " ".join([
                "Merged with MRN 456 on Oct 21 2014  4:44PM",
            ]),
            "ACTIVE_INACTIVE": "INACTIVE",
            "MERGED": "Y"
        },
        "456": {
            "MERGE_COMMENTS": " ".join([
                "Merged with MRN 345 Oct 17 2014 11:03AM",
                "Merged with MRN 345 on Oct 21 2014  4:44PM",
                "Merged with MRN 567 on Apr 14 2018  1:40PM"
            ]),
            "ACTIVE_INACTIVE": "INACTIVE",
            "MERGED": "Y"
        },
        "567": {
            "MERGE_COMMENTS": " ".join([
                "Merged with MRN 456 on Apr 14 2018  1:40PM",
            ]),
            "ACTIVE_INACTIVE": "ACTIVE",
            "MERGED": "Y"
        }
    }

    def setUp(self):
        self.masterfile_row = {
            "MERGED": "Y",

        }

    @mock.patch('intrahospital_api.update_demographics.get_masterfile_row')
    def test_basic_inactive_case(self, get_masterfile_row):
        """
        Pass in an inactive MRN, return the active MRN and the date it was merged.
        """
        get_masterfile_row.side_effect = lambda x: self.BASIC_MAPPING[x]
        active_mrn, merged_mrn_and_dates = update_demographics.get_active_mrn_and_merged_mrn_data('123')
        self.assertEqual(active_mrn, "234")
        self.assertEqual(
            merged_mrn_and_dates,
            [{
                "mrn": "123",
                "merge_comments": self.BASIC_MAPPING["123"]["MERGE_COMMENTS"],
            }]
        )

    @mock.patch('intrahospital_api.update_demographics.get_masterfile_row')
    def test_basic_active_case(self, get_masterfile_row):
        """
        Pass in an active MRN, return the active MRN and the date it was merged.
        """
        get_masterfile_row.side_effect = lambda x: self.BASIC_MAPPING[x]
        active_mrn, merged_mrn_and_dates = update_demographics.get_active_mrn_and_merged_mrn_data('234')
        self.assertEqual(active_mrn, "234")
        self.assertEqual(
            merged_mrn_and_dates,
            [{
                "mrn": "123",
                "merge_comments": self.BASIC_MAPPING["123"]["MERGE_COMMENTS"],
            }]
        )

    @mock.patch('intrahospital_api.update_demographics.get_masterfile_row')
    def test_uses_mrn_to_upstream_merge_data(self, get_masterfile_row):
        """
        Tests that if we use the mrn_to_upstream_merge_data dict the database is not called
        """
        get_masterfile_row.side_effect = lambda x: self.BASIC_MAPPING[x]
        active_mrn, merged_mrn_and_dates = update_demographics.get_active_mrn_and_merged_mrn_data(
            '123', self.BASIC_MAPPING
        )
        self.assertEqual(active_mrn, "234")
        self.assertEqual(
            merged_mrn_and_dates,
            [{
                "mrn": "123",
                "merge_comments": self.BASIC_MAPPING["123"]["MERGE_COMMENTS"],
            }]
        )
        self.assertFalse(get_masterfile_row.called)

    @mock.patch('intrahospital_api.update_demographics.get_masterfile_row')
    def test_crawls_nested_rows_from_branch(self, get_masterfile_row):
        """
        We pass in an inactive MRN not directly connected to the active MRN.

        We expect it to crawl the across the the MRNs it is connected with
        and to return the active MRN and merged data.
        """
        get_masterfile_row.side_effect = lambda mrn: self.COMPLEX_MAPPING[mrn]
        active_mrn, merged_data = update_demographics.get_active_mrn_and_merged_mrn_data(
            "345"
        )
        self.assertEqual(
            active_mrn, "567"
        )
        expected = [
            {
                "mrn": "345",
                "merge_comments": self.COMPLEX_MAPPING["345"]["MERGE_COMMENTS"]
            },
            {
                "mrn": "456",
                "merge_comments": self.COMPLEX_MAPPING["456"]["MERGE_COMMENTS"]
            },
        ]
        self.assertEqual(expected, merged_data)

    @mock.patch('intrahospital_api.update_demographics.get_masterfile_row')
    def test_crawls_nested_rows_from_trunk(self, get_masterfile_row):
        """
        We pass in an inactive MRN linked to an inactive MRN and an active MRN.

        We expect it to correctly decide which is the active MRN, and to return
        all inactive MRNs in the merged_mrn_data.
        """
        get_masterfile_row.side_effect = lambda mrn: self.COMPLEX_MAPPING[mrn]
        active_mrn, merged_data = update_demographics.get_active_mrn_and_merged_mrn_data(
            "456"
        )
        self.assertEqual(
            active_mrn, "567"
        )
        expected = [
            {
                "mrn": "345",
                "merge_comments": self.COMPLEX_MAPPING["345"]["MERGE_COMMENTS"]
            },
            {
                "mrn": "456",
                "merge_comments": self.COMPLEX_MAPPING["456"]["MERGE_COMMENTS"]
            },
        ]
        merged_data = sorted(merged_data, key=lambda x: x["mrn"])
        self.assertEqual(expected, merged_data)

    @mock.patch('intrahospital_api.update_demographics.get_masterfile_row')
    def test_handles_active_mrns(self, get_masterfile_row):
        """
        We pass in an active MRN linked to an inactive MRN that is linked to an inactive
        MRN.

        We expect it to correctly recognise it is an inactive MRN and return
        all related MRNs as merged_mrn_data.
        """
        get_masterfile_row.side_effect = lambda mrn: self.COMPLEX_MAPPING[mrn]
        active_mrn, merged_data = update_demographics.get_active_mrn_and_merged_mrn_data(
            "567"
        )
        self.assertEqual(
            active_mrn, "567"
        )
        expected = [
            {
                "mrn": "345",
                "merge_comments": self.COMPLEX_MAPPING["345"]["MERGE_COMMENTS"]
            },
            {
                "mrn": "456",
                "merge_comments": self.COMPLEX_MAPPING["456"]["MERGE_COMMENTS"]
            },
        ]
        merged_data = sorted(merged_data, key=lambda x: x["mrn"])
        self.assertEqual(expected, merged_data)

    @mock.patch('intrahospital_api.update_demographics.get_masterfile_row')
    @mock.patch('intrahospital_api.update_demographics.logger')
    def test_no_active_mrn(
        self, logger, get_masterfile_row
    ):
        """
        For an MRN if there are no active rows we should log an error
        """
        basic_mapping = copy.deepcopy(self.BASIC_MAPPING)
        basic_mapping["234"]["ACTIVE_INACTIVE"] = "INACTIVE"
        get_masterfile_row.side_effect = lambda x: basic_mapping[x]
        active_mrn, merged_data = update_demographics.get_active_mrn_and_merged_mrn_data(
            "123"
        )
        self.assertEqual(active_mrn, "123")
        self.assertEqual(merged_data, [])
        logger.warn.assert_called_once_with(
            "Unable to find an active MRN for 123"
        )

    @mock.patch('intrahospital_api.update_demographics.get_masterfile_row')
    @mock.patch('intrahospital_api.update_demographics.logger')
    def test_only_active_mrns(
        self, logger, get_masterfile_row
    ):
        """
        For an MRN if there are only active rows we should log an error
        """
        basic_mapping = copy.deepcopy(self.BASIC_MAPPING)
        basic_mapping["123"]["ACTIVE_INACTIVE"] = "ACTIVE"
        get_masterfile_row.side_effect = lambda x: basic_mapping[x]
        active_mrn, merged_data = update_demographics.get_active_mrn_and_merged_mrn_data(
            "123"
        )
        self.assertEqual(active_mrn, "123")
        self.assertEqual(merged_data, [])
        logger.warn.assert_called_once_with(
            "Merge exception raised for 123 with 'Multiple active related MRNs (123, 234) found for 123'"
        )

    @mock.patch('intrahospital_api.update_demographics.get_masterfile_row')
    def test_raises_exception_if_the_patient_is_not_found(
        self, get_masterfile_row
    ):
        get_masterfile_row.return_value = None
        with self.assertRaises(update_demographics.CernerPatientNotFoundException) as err:
            update_demographics.get_active_mrn_and_merged_mrn_data('123')
        self.assertEqual(str(err.exception), "Unable to find a masterfile row for 123")

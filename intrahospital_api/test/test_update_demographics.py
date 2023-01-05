from unittest import mock
import datetime
from opal.core.test import OpalTestCase
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


@mock.patch('intrahospital_api.update_demographics.get_masterfile_row')
class GetActiveMrnAndMergedMrnDataTestCase(OpalTestCase):
    BASIC_MAPPING = {
        "123": {
            "MERGE_COMMENTS": "Merged with MRN 234 on Oct 20 2014  4:44PM",
            "ACTIVE_INACTIVE": "INACTIVE"
        },
        "234": {
            "MERGE_COMMENTS": "Merged with MRN 123 on Oct 21 2014  4:44PM",
            "ACTIVE_INACTIVE": "ACTIVE"
        }

    }

    COMPLEX_MAPPING = {
        "345": {
            "MERGE_COMMENTS": " ".join([
                "Merged with MRN 456 on Oct 21 2014  4:44PM",
            ]),
            "ACTIVE_INACTIVE": "INACTIVE"
        },
        "456": {
            "MERGE_COMMENTS": " ".join([
                "Merged with MRN 345 Oct 17 2014 11:03AM",
                "Merged with MRN 345 on Oct 21 2014  4:44PM",
                "Merged with MRN 567 on Apr 14 2018  1:40PM"
            ]),
            "ACTIVE_INACTIVE": "INACTIVE"
        },
        "567": {
            "MERGE_COMMENTS": " ".join([
                "Merged with MRN 456 on Apr 14 2018  1:40PM",
            ]),
            "ACTIVE_INACTIVE": "ACTIVE"
        }
    }

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
                "upstream_merge_datetime": timezone.make_aware(datetime.datetime(
                    2014, 10, 20, 16, 44
                ))
            }]
        )

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
                "upstream_merge_datetime": timezone.make_aware(datetime.datetime(
                    2014, 10, 20, 16, 44
                ))
            }]
        )

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
                "upstream_merge_datetime": timezone.make_aware(datetime.datetime(
                    2014, 10, 21, 16, 44
                )),
                "merge_comments": self.COMPLEX_MAPPING["345"]["MERGE_COMMENTS"]
            },
            {
                "mrn": "456",
                "upstream_merge_datetime": timezone.make_aware(datetime.datetime(
                    2018, 4, 14, 13, 40
                )),
                "merge_comments": self.COMPLEX_MAPPING["456"]["MERGE_COMMENTS"]
            },
        ]
        self.assertEqual(expected, merged_data)

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
                "upstream_merge_datetime": timezone.make_aware(datetime.datetime(
                    2014, 10, 21, 16, 44
                )),
                "merge_comments": self.COMPLEX_MAPPING["345"]["MERGE_COMMENTS"]
            },
            {
                "mrn": "456",
                "upstream_merge_datetime": timezone.make_aware(datetime.datetime(
                    2018, 4, 14, 13, 40
                )),
                "merge_comments": self.COMPLEX_MAPPING["456"]["MERGE_COMMENTS"]
            },
        ]
        merged_data = sorted(merged_data, key=lambda x: x["mrn"])
        self.assertEqual(expected, merged_data)

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
                "upstream_merge_datetime": timezone.make_aware(datetime.datetime(
                    2014, 10, 21, 16, 44
                )),
                "merge_comments": self.COMPLEX_MAPPING["345"]["MERGE_COMMENTS"]
            },
            {
                "mrn": "456",
                "upstream_merge_datetime": timezone.make_aware(datetime.datetime(
                    2018, 4, 14, 13, 40
                )),
                "merge_comments": self.COMPLEX_MAPPING["456"]["MERGE_COMMENTS"]
            },
        ]
        merged_data = sorted(merged_data, key=lambda x: x["mrn"])
        self.assertEqual(expected, merged_data)

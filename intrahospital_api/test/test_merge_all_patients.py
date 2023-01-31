from unittest import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import merge_all_patients


class MergeAllPatientsTestCase(OpalTestCase):
    @mock.patch(".".join([
        'intrahospital_api.management.commands',
        'merge_all_patients.update_demographics.get_active_mrn_and_merged_mrn_data'
    ]))
    def test_handle(self, get_active_mrn_and_merged_mrn_data):
        cmd = merge_all_patients.Command()
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="123"
        )
        patient.masterfilemeta_set.create(
            merged='Y', active_inactive='ACTIVE'
        )
        get_active_mrn_and_merged_mrn_data.return_value = (
            "123", [{'mrn': "234", 'merge_comments': 'merged yesterday'}],
        )
        cmd.handle()
        merged_mrn = patient.mergedmrn_set.get()
        self.assertEqual(
            merged_mrn.mrn, "234"
        )
        self.assertEqual(
            merged_mrn.merge_comments, "merged yesterday"
        )

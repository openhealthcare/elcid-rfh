from unittest import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import merge_patients_since
from intrahospital_api import constants
from plugins.monitoring.models import Fact

root = 'intrahospital_api.management.commands.merge_patients_since'

@mock.patch(f'{root}.update_demographics.get_all_merged_mrns_since')
@mock.patch(f'{root}.update_demographics.check_and_handle_upstream_merges_for_mrns')
@mock.patch(f'{root}.update_demographics.logger.error')
class MergePatientsSinceTestCase(OpalTestCase):
	def test_handle(
		self, error, check_and_handle_upstream_merges_for_mrns, get_all_merged_mrns_since
	):
		cmd = merge_patients_since.Command()
		cmd.handle()
		self.assertTrue(
			Fact.objects.filter(label=constants.MERGE_LOAD_MINUTES).exists()
		)
		self.assertTrue(
			Fact.objects.filter(label=constants.TOTAL_MERGE_COUNT).exists()
		)
		self.assertFalse(error.called)

	def test_raises(
		self, error, check_and_handle_upstream_merges_for_mrns, get_all_merged_mrns_since
	):
		check_and_handle_upstream_merges_for_mrns.side_effect = ValueError('Boom')
		cmd = merge_patients_since.Command()
		cmd.handle()
		self.assertTrue(error.called)

	@mock.patch(f'{root}.utils.send_email')
	def test_sends_email(
		self,
		send_email,
		error,
		check_and_handle_upstream_merges_for_mrns,
		get_all_merged_mrns_since,
	):
		get_all_merged_mrns_since.return_value = list(
			range(merge_patients_since.UNEXPECTED_VOLUMES_THRESHOLD + 1)
		)
		cmd = merge_patients_since.Command()
		cmd.handle()
		self.assertTrue(check_and_handle_upstream_merges_for_mrns.called)
		send_email.assert_called_once_with(
			'200001 being processed by merge_patients_since',
			"\n".join([
				'get_all_merged_mrns_since returned 200001 MRNs',
				f'This is more than we would expect and higher than the threshold {merge_patients_since.UNEXPECTED_VOLUMES_THRESHOLD}',
				'Please log in and check that the server is handling this unexpected volume.'
			])
		)

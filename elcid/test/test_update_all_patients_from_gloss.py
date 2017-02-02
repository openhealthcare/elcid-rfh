import mock

from opal.core.test import OpalTestCase
from elcid.management.commands.update_all_patients_from_gloss import Command


class UpdateFromGlossManagementCommandTestCase(OpalTestCase):
    @mock.patch(
        "elcid.management.commands.update_all_patients_from_gloss.gloss_api"
    )
    def test_updates_all_patients(self, gloss_api):
        patient, episode = self.new_patient_and_episode_please()
        patient.demographics_set.update(hospital_number="007")
        Command().handle()
        gloss_api.patient_query.assert_called_once_with(("007",))

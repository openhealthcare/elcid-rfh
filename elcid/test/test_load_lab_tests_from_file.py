from opal.core.test import OpalTestCase
import mock
from elcid.management.commands import load_from_file as loader


class LoadLabTestsFromFileTestCase(OpalTestCase):

    @mock.patch(
        'elcid.management.commands.load_from_file.json'
    )
    @mock.patch(
        'elcid.management.commands.load_from_file.gloss_api.bulk_create_from_gloss_response'
    )
    def test_load_lab_tests(self, bulk_create, json):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(hospital_number="234")
        json.load.return_value = dict(
            hospital_number="123"
        )
        loader.Command().handle(filename="some_file.json", patient=1)
        bulk_create.assert_called_once_with(dict(
            hospital_number="234"
        ))

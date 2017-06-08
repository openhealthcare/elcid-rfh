from opal.core.test import OpalTestCase
import mock
from elcid.management.commands import load_in_subrecords as loader


class LoadInSubrecordsTestCase(OpalTestCase):
    @mock.patch('elcid.management.commands.load_in_subrecords.open', create=True)
    @mock.patch('elcid.management.commands.load_in_subrecords.os.path.exists')
    @mock.patch('elcid.management.commands.load_in_subrecords.json.loads')
    def test_load_with_patient_id(
        self, loads, join, open
    ):
        patient, _ = self.new_patient_and_episode_please()
        loads.return_value = {
            "lab_test": [
                dict(
                    id=10,
                    status=None,
                    updated=None,
                    consistency_token=None,
                    lab_test_type="GNR",
                    extras=dict(
                        aerobic=True,
                        source="peripheral"
                    ),
                    result=dict(
                        name="result",
                        observation_type="GNRResult"
                    )
                )
            ]
        }

        loader.Command().handle(
            filename="some_file.html",
            user=self.user.username,
            patient=patient.id
        )
        lab_test = patient.labtest_set.get()

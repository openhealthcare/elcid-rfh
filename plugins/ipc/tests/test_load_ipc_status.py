from unittest.mock import patch
from django.contrib.auth.models import User
from opal.core.test import OpalTestCase
from plugins.ipc.management.commands import load_ipc_status
from plugins.ipc import episode_categories


class LoadIPCTestCase(OpalTestCase):
    def setUp(self):
        self.upstream_row = {
            k: None for k in load_ipc_status.MAPPING.keys()
        }
        self.upstream_row["Patient_Number"] = "123"
        self.upstream_row["Comment"] = "A comment"
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(
            hospital_number="123"
        )
        User.objects.create(username='ohc')
        self.cmd = load_ipc_status.Command()

    @patch('plugins.ipc.management.commands.load_ipc_status.ProdAPI')
    def test_creates(self, ProdAPI):
        ProdAPI.return_value.execute_hospital_query.return_value = [self.upstream_row]
        self.cmd.handle()
        self.assertTrue(
            self.patient.episode_set.filter(
                category_name=episode_categories.IPCEpisode.display_name
            ).exists()
        )
        ipc_status = self.patient.ipcstatus_set.get()
        # Make sure the patient's ipc status has been updated by the row
        self.assertEqual(ipc_status.comments, "A comment")

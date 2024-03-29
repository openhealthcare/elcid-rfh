from unittest.mock import patch
from django.contrib.auth.models import User
from opal.core.test import OpalTestCase
from opal.models import Patient
from plugins.ipc.management.commands import load_ipc_status
from plugins.ipc import episode_categories
from elcid import episode_categories as elcid_episode_categories


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

    @patch('plugins.ipc.management.commands.load_ipc_status.ProdAPI')
    @patch('intrahospital_api.loader.create_rfh_patient_from_hospital_number')
    def test_creates_patient(self, create_rfh_patient_from_hospital_number, ProdAPI):
        ProdAPI.return_value.execute_hospital_query.return_value = [self.upstream_row]
        self.upstream_row["Patient_Number"] = "234"
        def create_patient():
            patient, episode = self.new_patient_and_episode_please()
            patient.demographics_set.update(hospital_number="234")
            episode.category_name = elcid_episode_categories.InfectionService.display_name
            episode.save()
            return patient

        create_rfh_patient_from_hospital_number.side_effect = lambda x, y: create_patient()
        self.cmd.handle()
        self.assertTrue(
            Patient.objects.filter(
                demographics__hospital_number="234"
            ).filter(
                episode__category_name = episode_categories.IPCEpisode.display_name
            ).exists()
        )

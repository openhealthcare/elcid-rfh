import mock
from opal.core.test import OpalTestCase
from intrahospital_api import tasks, models


class TaskTestCase(OpalTestCase):
    @mock.patch("intrahospital_api.loader")
    def test_load(self, loader):
        patient, _ = self.new_patient_and_episode_please()
        ip = models.InitialPatientLoad(patient=patient)
        ip.start()
        tasks.load(patient, ip)
        loader.async_load_patient.assert_called_once_with(
            patient.id, ip.id
        )

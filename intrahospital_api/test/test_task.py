from django.utils import timezone
from intrahospital_api.models import InitialPatientLoad
from intrahospital_api import tasks
from opal.core.test import OpalTestCase
import mock


@mock.patch("intrahospital_api.loader")
class TaskTestCase(OpalTestCase):
    def test_load(self, loader):
        patient, _ = self.new_patient_and_episode_please()
        ipl = InitialPatientLoad(patient=patient)
        ipl.start()
        tasks.load(patient, ipl)
        loader.async_load_patient.assert_called_once_with(
            patient, ipl
        )

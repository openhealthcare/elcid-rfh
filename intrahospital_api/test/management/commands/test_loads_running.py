import json
import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import batch_test_load_running
from intrahospital_api.models import (
    InitialPatientLoad, BatchPatientLoad
)


class AnyLoadsRunningTestCase(OpalTestCase):
    def loads_running(self):
        batch_command = batch_test_load_running.Command()
        with mock.patch.object(batch_command, "stdout") as stdout:
            batch_command.handle()
        return json.loads(stdout.write.call_args[0][0])["status"]

    def test_any_initial_patient_loads_running(self):
        patient, _ = self.new_patient_and_episode_please()
        ipl = InitialPatientLoad(patient=patient)
        ipl.start()
        self.assertTrue(self.loads_running())
        ipl.complete()
        self.assertFalse(self.loads_running())

    def test_any_batch_loads_running(self):
        bpl = BatchPatientLoad(service_name="something")
        bpl.start()
        self.assertTrue(self.loads_running())
        bpl.complete()
        self.assertFalse(self.loads_running())

    def test_no_loads(self):
        self.assertFalse(self.loads_running())


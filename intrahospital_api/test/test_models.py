from mock import PropertyMock, patch
from opal.core.test import OpalTestCase
from intrahospital_api import models
from intrahospital_api import exceptions


class InitialPatientLoadTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(hospital_number="AAA")
        self.ipl = models.InitialPatientLoad(patient=self.patient)
        self.ipl.start()

    def test_str_running(self):
        self.assertIn(self.ipl.RUNNING, str(self.ipl))
        self.assertIn("AAA", str(self.ipl))

    def test_str_stopped(self):
        self.ipl.complete()
        self.assertIn(self.ipl.SUCCESS, str(self.ipl))
        self.assertIn("AAA", str(self.ipl))
        with patch.object(
            models.InitialPatientLoad, 'duration', new_callable=PropertyMock
        ) as m:
            m.return_value = ""
            str(self.ipl)
            self.assertTrue(m.called)

    def test_update_from_dict(self):
        self.ipl.update_from_dict(dict(state=self.ipl.SUCCESS))
        self.assertEqual(self.ipl.state, self.ipl.RUNNING)


class BatchPatientLoadTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.bpl = models.BatchPatientLoad(service_name="lab tests")
        self.bpl.start()

    def test_service_name(self):
        self.assertIn("lab tests", str(self.bpl))

    def test_unicode_running(self):
        self.assertIn(self.bpl.RUNNING, str(self.bpl))

    def test_str_stopped(self):
        self.bpl.complete()
        self.assertIn(self.bpl.SUCCESS, str(self.bpl))
        with patch.object(
            models.BatchPatientLoad, 'duration', new_callable=PropertyMock
        ) as m:
            m.return_value = ""
            str(self.bpl)
            self.assertTrue(m.called)

    def test_save_when_there_is_a_batch_load_running(self):
        bpl2 = models.BatchPatientLoad(service_name="lab tests")
        with self.assertRaises(exceptions.BatchLoadError) as e:
            bpl2.start()
        er = "Trying to start a batch for lab tests when {} is still running"
        expected = er.format(
            self.bpl.id
        )
        self.assertEqual(str(e.exception), expected)

    def test_save_when_there_is_no_batch_load(self):
        self.bpl.complete()
        self.assertEqual(self.bpl.state, self.bpl.SUCCESS)
        bpl2 = models.BatchPatientLoad(service_name="lab tests")
        bpl2.start()
        self.assertEqual(bpl2.state, self.bpl.RUNNING)



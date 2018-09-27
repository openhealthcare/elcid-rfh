from mock import PropertyMock, patch
from opal.core.test import OpalTestCase
from intrahospital_api import models


class InitialPatientLoadTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(hospital_number="AAA")
        self.ipl = models.InitialPatientLoad(patient=self.patient)
        self.ipl.start()

    def test_unicode_running(self):
        self.assertIn(self.ipl.RUNNING, unicode(self.ipl))
        self.assertIn("AAA", unicode(self.ipl))

    def test_unicode_stopped(self):
        self.ipl.complete()
        self.assertIn(self.ipl.SUCCESS, unicode(self.ipl))
        self.assertIn("AAA", unicode(self.ipl))
        with patch.object(
            models.InitialPatientLoad, 'duration', new_callable=PropertyMock
        ) as m:
            m.return_value = ""
            unicode(self.ipl)
            self.assertTrue(m.called)

    def test_update_from_dict(self):
        self.ipl.update_from_dict(dict(state=self.ipl.SUCCESS))
        self.assertEqual(self.ipl.state, self.ipl.RUNNING)


class BatchPatientLoadTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.bpl = models.BatchPatientLoad()
        self.bpl.start()

    def test_unicode_running(self):
        self.assertIn(self.bpl.RUNNING, unicode(self.bpl))

    def test_unicode_stopped(self):
        self.bpl.complete()
        self.assertIn(self.bpl.SUCCESS, unicode(self.bpl))
        with patch.object(
            models.BatchPatientLoad, 'duration', new_callable=PropertyMock
        ) as m:
            m.return_value = ""
            unicode(self.bpl)
            self.assertTrue(m.called)

from mock import PropertyMock, patch
import datetime
from django.utils import timezone
from opal.core.test import OpalTestCase
from intrahospital_api import models


@patch("intrahospital_api.models.timezone.now")
class PatientLoadTestCase(OpalTestCase):
    def setUp(self, *args, **kwargs):
        self.patient, _ = self.new_patient_and_episode_please()
        self.now = timezone.now()
        self.a_min_ago = self.now - datetime.timedelta(seconds=60)

    def test_start(self, now):
        now.return_value = self.now
        ipl = models.InitialPatientLoad(patient=self.patient)
        ipl.start()
        ipl = models.InitialPatientLoad.objects.get(id=ipl.id)
        self.assertTrue(
            ipl.started,
            self.now
        )
        self.assertEqual(ipl.state, ipl.RUNNING)

    @patch("intrahospital_api.models.logger.info")
    def test_complete(self, info, now):
        now.side_effect = [self.a_min_ago, self.now]
        ipl = models.InitialPatientLoad(patient=self.patient)
        ipl.start()
        ipl.complete()
        ipl = models.InitialPatientLoad.objects.get(id=ipl.id)
        self.assertEqual(ipl.started, self.a_min_ago)
        self.assertEqual(ipl.stopped, self.now)
        self.assertEqual(ipl.state, ipl.SUCCESS)
        info.assert_called_once_with(
            'InitialPatientLoad 1 succeeded in 0:01:00'
        )

    @patch("intrahospital_api.models.logger.info")
    def test_fail(self, info, now):
        now.side_effect = [self.a_min_ago, self.now]
        ipl = models.InitialPatientLoad(patient=self.patient)
        ipl.start()
        ipl.failed()
        ipl = models.InitialPatientLoad.objects.get(id=ipl.id)
        self.assertEqual(ipl.started, self.a_min_ago)
        self.assertEqual(ipl.stopped, self.now)
        self.assertEqual(ipl.state, ipl.FAILURE)
        info.assert_called_once_with('InitialPatientLoad 1 failed in 0:01:00')


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

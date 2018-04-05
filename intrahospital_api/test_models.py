import mock
import datetime
from django.utils import timezone
from opal.core.test import OpalTestCase
from intrahospital_api import models


@mock.patch("intrahospital_api.models.timezone")
class InitialPatientLoadTestCase(OpalTestCase):
    def setUp(self):
        super(InitialPatientLoadTestCase, self).setUp()
        patient, _ = self.new_patient_and_episode_please()
        self.ipl = models.InitialPatientLoad(
            patient=patient
        )
        self.now = timezone.make_aware(
            datetime.datetime(2017, 1, 1), timezone.get_current_timezone()
        )
        self.before = self.now - datetime.timedelta(1)

    def test_start(self, tz):
        tz.now.return_value = self.now
        self.ipl.start()
        self.assertEqual(self.ipl.started, self.now)
        self.assertEqual(
            self.ipl.state, models.InitialPatientLoad.RUNNING
        )

    def test_complete(self, tz):
        tz.now.return_value = self.now
        self.ipl.started = self.before
        self.ipl.save()
        self.ipl.complete()
        self.assertEqual(
            self.ipl.state, models.InitialPatientLoad.SUCCESS
        )
        self.assertEqual(
            self.ipl.stopped, self.now
        )

    def test_failed(self, tz):
        tz.now.return_value = self.now
        self.ipl.started = self.before
        self.ipl.save()
        self.ipl.failed()
        self.assertEqual(
            self.ipl.state, models.InitialPatientLoad.FAILURE
        )
        self.assertEqual(
            self.ipl.stopped, self.now
        )

    def test_duration(self, tz):
        tz.now.return_value = self.now
        self.ipl.started = self.before
        self.ipl.stopped = self.now
        self.ipl.save()
        self.assertEqual(
            self.ipl.duration, datetime.timedelta(1)
        )

    def test_str(self, tz):
        tz.now.return_value = self.now
        self.ipl.started = self.before
        self.assertEqual(
            str(self.ipl), 'initial patient load 1 31/12/2016 00:00:00 None'
        )


@mock.patch("intrahospital_api.models.timezone")
class BatchPatientLoadTestCase(OpalTestCase):
    def setUp(self):
        super(BatchPatientLoadTestCase, self).setUp()
        patient, _ = self.new_patient_and_episode_please()
        self.bpl = models.BatchPatientLoad()
        self.now = timezone.make_aware(
            datetime.datetime(2017, 1, 1), timezone.get_current_timezone()
        )
        self.before = self.now - datetime.timedelta(1)

    def test_start(self, tz):
        tz.now.return_value = self.now
        self.bpl.start()
        self.assertEqual(self.bpl.started, self.now)
        self.assertEqual(
            self.bpl.state, models.BatchPatientLoad.RUNNING
        )

    def test_complete(self, tz):
        tz.now.return_value = self.now
        self.bpl.started = self.before
        self.bpl.save()
        self.bpl.complete()
        self.assertEqual(
            self.bpl.state, models.BatchPatientLoad.SUCCESS
        )
        self.assertEqual(
            self.bpl.stopped, self.now
        )

    def test_failed(self, tz):
        tz.now.return_value = self.now
        self.bpl.started = self.before
        self.bpl.save()
        self.bpl.failed()
        self.assertEqual(
            self.bpl.state, models.BatchPatientLoad.FAILURE
        )
        self.assertEqual(
            self.bpl.stopped, self.now
        )

    def test_duration(self, tz):
        tz.now.return_value = self.now
        self.bpl.started = self.before
        self.bpl.stopped = self.now
        self.bpl.save()
        self.assertEqual(
            self.bpl.duration, datetime.timedelta(1)
        )

    def test_str(self, tz):
        tz.now.return_value = self.now
        self.bpl.started = self.before
        self.assertEqual(
            str(self.bpl), 'batch patient load 31/12/2016 00:00:00 None None'
        )

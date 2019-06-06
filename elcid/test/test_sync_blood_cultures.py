import datetime
from opal.core.test import OpalTestCase
from elcid import models
from elcid.management.commands import sync_blood_cultures


class SyncBloodCulturesTestCase(OpalTestCase):
    def setUp(self):
        super().setUp()
        self.patient, _ = self.new_patient_and_episode_please()

    def test_synch_blood_cultures(self):
        extras = {
            'aerobic': True,
            'isolate': '1',
            'lab_number': '17L381410',
            'source': 'IV Line'
        }
        gram_stain = models.GramStain(patient=self.patient)
        gram_stain.update_from_dict(dict(
            lab_test_type=models.GramStain.get_display_name(),
            result=dict(result="Yeast"),
        ), self.user)
        gram_stain.extras = extras
        gram_stain.datetime_ordered = datetime.datetime(
            2018, 10, 1, 10, 12
        )
        gram_stain.save()

        sync_blood_cultures.sync_blood_cultures(self.patient)
        new_lab_test = self.patient.bloodcultureset_set.get()

        self.assertEqual(
            new_lab_test.date_ordered,
            datetime.date(2018, 10, 1)
        )

        self.assertEqual(
            new_lab_test.source, 'IV Line'
        )

        self.assertEqual(
            new_lab_test.lab_number, '17L381410'
        )

        isolate = new_lab_test.isolates.get()

        self.assertEqual(
            isolate.aerobic_or_anaerobic, isolate.AEROBIC
        )

        self.assertEqual(
            isolate.gram_stain, "Yeast"
        )
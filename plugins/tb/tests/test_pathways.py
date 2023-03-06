from opal.core.test import OpalTestCase
from elcid import models
from plugins.tb import pathways


class ConditionalHelpStepTestCase(OpalTestCase):
    def test_condition_init(self):
        some_step = pathways.ConditionalHelpStep(
            models.Demographics,
            condition="a == 1"
        )
        self.assertEqual(
            some_step.condition,
            "a == 1"
        )


class NationalityAndLanguageTestCase(OpalTestCase):
    def setUp(self):
        self.patient, self.episode = self.new_patient_and_episode_please()
        self.pathway = pathways.NationalityAndLanguage()

    def test_nulls_out_communication_considerations(self):
        data = {
            "demographics": [{'birth_place': None}],
            "nationality": [{
                "id": self.patient.nationality_set.get().id,
                "arrival_in_the_uk": "1956",
                "previous_mrn": "234"
            }]
        }
        self.patient.nationality_set.update(
            previous_mrn="234"
        )
        self.patient.communinicationconsiderations_set.update(
            previous_mrn="234"
        )
        self.pathway.save(
            data,
            episode=self.episode,
            patient=self.patient
        )
        self.assertIsNone(
            self.patient.communinicationconsiderations_set.get().previous_mrn
        )
        self.assertIsNone(
            self.patient.nationality_set.get().previous_mrn
        )

    def test_nulls_out_nationality(self):
        data = {
            "demographics": [{'birth_place': None}],
            "communication_considerations": [{
                "arrival_in_the_uk": "1956",
                "previous_mrn": "234"
            }]
        }
        self.patient.nationality_set.update(
            previous_mrn="234"
        )
        self.pathway.save(
            data,
            episode=self.episode,
            patient=self.patient
        )
        self.assertIsNone(
            self.patient.nationality_set.get().previous_mrn
        )

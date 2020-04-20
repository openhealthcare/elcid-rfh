from opal.core.test import OpalTestCase
from elcid import models
from plugins.tb import pathways
from plugins.tb import constants as tb_constants


class AddTBPatientTestCase(OpalTestCase):
    def setUp(self):
        self.pathway = pathways.AddTbPatientPathway()
        self.patient, self.episode = self.new_patient_and_episode_please()

    def test_add_patient(self):
        self.pathway.save({}, self.user, self.patient)
        self.assertEqual(
            self.patient.episode_set.count(), 2
        )
        self.assertEqual(
            self.patient.episode_set.filter(
                tagging__value=tb_constants.TB_TAG
            ).count(), 1
        )

    def test_add_same_patient(self):
        self.episode.category_name = "TB"
        self.episode.set_tag_names([tb_constants.TB_TAG], self.user)
        self.pathway.save({}, self.user, self.patient)
        e = self.patient.episode_set.get()
        self.assertEqual(
            e.get_tag_names(self.user), [tb_constants.TB_TAG]
        )


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

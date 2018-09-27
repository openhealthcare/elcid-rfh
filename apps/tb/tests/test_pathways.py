from opal.core.test import OpalTestCase
from elcid import models
from apps.tb import pathways


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

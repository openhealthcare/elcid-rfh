from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import reset_ethnicities
from opal.models import Ethnicity
import mock


class ResetEthnicitiesTestCase(OpalTestCase):
    def add_ethnicity(self, *args, **kwargs):
        Ethnicity.objects.create(name="White - Any Other White Background")

    @mock.patch(
        'intrahospital_api.management.commands.reset_ethnicities.load_lookuplist'
    )
    def test_reset_ethnicities(self, load_lookuplist):
        load_lookuplist.side_effect = self.add_ethnicity
        patient, episode = self.new_patient_and_episode_please()
        demographics = patient.demographics_set.first()

        # create a new ethncity
        Ethnicity.objects.create(name="some ethnicity")
        demographics.ethnicity = "some ethnicity"
        demographics.save()
        cmd = reset_ethnicities.Command()
        cmd.handle()

        reloaded_demographics = patient.demographics_set.get()

        # we should still have the ethnicity
        self.assertEqual(
            reloaded_demographics.ethnicity, "some ethnicity"
        )

        # we should only have one ethnicity, the new ethnicity
        e = Ethnicity.objects.get()
        self.assertEqual(
            e.name, "White - Any Other White Background"
        )

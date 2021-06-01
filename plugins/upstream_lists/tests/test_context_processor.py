"""
Unittest for plugins.upstream_lists.context_processors
"""
import datetime
from opal.core.test import OpalTestCase
from opal.models import Clinical_advice_reason_for_interaction
from elcid.models import MicrobiologyInput
from plugins.icu.models import ICUHandoverLocation
from plugins.upstream_lists import context_processors


class UpstreamListsTestCase(OpalTestCase):

    def test_lists(self):
        Clinical_advice_reason_for_interaction.objects.create(
            name=MicrobiologyInput.ICU_REASON_FOR_INTERACTION
        )
        p, e = self.new_patient_and_episode_please()
        ICUHandoverLocation.objects.create(
            ward='South',
            patient=p,
            admitted=datetime.date.today()
        )

        lists = context_processors.upstream_lists(None)

        self.assertEqual(
            ('#/list/upstream/South', 'Auto ICU South'),
            lists['upstream_lists'][0]
        )

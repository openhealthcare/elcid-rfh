"""
Unittest for plugins.upstream_lists.context_processors
"""
from opal.core.test import OpalTestCase

from plugins.icu.models import ICUHandoverLocation

from plugins.upstream_lists import context_processors


class UpstreamListsTestCase(OpalTestCase):

    def test_lists(self):
        p, e = self.new_patient_and_episode_please()
        ICUHandoverLocation.objects.create(ward='South', patient=p)

        lists = context_processors.upstream_lists(None)

        self.assertEqual(
            ('#/list/upstream/South', 'Auto ICU South'),
            lists['upstream_lists'][0]
        )

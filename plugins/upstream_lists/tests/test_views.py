"""
Unittests for plugins.upstream_lists.views
"""
from opal.core.test import OpalTestCase

from plugins.upstream_lists import views


class UpstreamListTemplateViewTestCase(OpalTestCase):

    def test_list_is_read_only(self):
        view = views.UpstreamListTemplateView()
        view.request = self.rf.get('/upstream/south.html')
        view.request.user = self.user

        ctx = view.get_context_data(slug='south')

        self.assertEqual(True, ctx['patient_list']['is_read_only'])

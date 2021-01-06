"""
Unittests for plugins.upstream_lists.api
"""
import json
from unittest import mock

from opal.core.test import OpalTestCase

from plugins.upstream_lists import api


class UpstreamListTestCase(OpalTestCase):

    def test_retrieve(self):
        API = api.UpstreamPatientListViewSet()
        mock_request = mock.MagicMock(name='Mock Request')
        episodes = json.loads(API.retrieve(mock_request, pk='south').content)
        self.assertEqual([], episodes)

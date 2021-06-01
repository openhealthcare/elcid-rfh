"""
Unittests for plugins.upstream_lists.api
"""
import json
from unittest import mock

from opal.models import Clinical_advice_reason_for_interaction
from opal.core.test import OpalTestCase

from elcid.models import MicrobiologyInput
from plugins.upstream_lists import api


class UpstreamListTestCase(OpalTestCase):

    def test_retrieve(self):
        Clinical_advice_reason_for_interaction.objects.create(
            name=MicrobiologyInput.ICU_REASON_FOR_INTERACTION
        )
        API = api.UpstreamPatientListViewSet()
        mock_request = mock.MagicMock(name='Mock Request')
        episodes = json.loads(API.retrieve(mock_request, pk='south').content)
        self.assertEqual([], episodes)

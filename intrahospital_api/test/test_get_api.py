import mock
from django.test import override_settings
from opal.core.test import OpalTestCase
from intrahospital_api import get_api


@override_settings(INTRAHOSPITAL_API="something")
@mock.patch('intrahospital_api.import_string')
class GetApiTestCase(OpalTestCase):
    def test_get_api(self, import_string):
        import_string().return_value = "some api"
        result = get_api()
        self.assertEqual(result, "some api")
        self.assertEqual(import_string.call_args[0], ("something",))

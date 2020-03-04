from opal.core.test import OpalTestCase
from django.template import Template, Context
from plugins.labtests.templatetags import key_investigations

class TestCase(OpalTestCase):
    def test_key_investigations_default_arguments(self):
        url = "some_url"
        expected = {
            "url_base": url,
            "title": 'Key Investigations',
            "body_class": None,
            "icon": "fa fa-crosshairs"
        }
        self.assertEqual(
            key_investigations.key_investigations(url),
            expected
        )

    def test_key_investigations_passed_in_arguments(self):
        url = "some_url"
        expected = {
            "url_base": url,
            "title": "some title",
            "body_class": "some_body_class",
            "icon": "some_icon"
        }
        result = key_investigations.key_investigations(
            url,
            title="some title",
            body_class="some_body_class",
            icon="some_icon"

        )
        self.assertEqual(result, expected)

    def test_render(self):
        tpl = Template('{% load key_investigations %}{% key_investigations "/api/v0.1/tb_test_summary/" body_class="panel-footer" %}')
        rendered = tpl.render(Context({}))
        self.assertIsNotNone(rendered)

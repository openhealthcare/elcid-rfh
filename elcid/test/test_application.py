from opal.core.test import OpalTestCase
from django.test import override_settings
from elcid import Application


class ApplicationTestCase(OpalTestCase):
    def test_get_menu_items(self):
        menu_items = Application.get_menu_items()
        expected_hrefs = [menu_item.href for menu_item in menu_items]
        self.assertIn("/pathway/#/add_patient", expected_hrefs)

    def test_make_sure_we_dont_change_a_global_object(self):
        # make sure we don't change the list as it appears on
        # the application object
        menu_items_1 = Application.get_menu_items()
        menu_items_2 = Application.get_menu_items()
        self.assertEqual(menu_items_1, menu_items_2)

    @override_settings(EMAIL_JS_ERRORS=True)
    def test_get_javascripts_with_error_emails(self):
        scripts = Application.get_javascripts()
        self.assertIn(
            'js/elcid/services/exception_handler.js', scripts
        )

    @override_settings(EMAIL_JS_ERRORS=False)
    def test_get_javascripts_without_error_emails(self):
        scripts = Application.get_javascripts()
        self.assertNotIn(
            'js/elcid/services/exception_handler.js', scripts
        )

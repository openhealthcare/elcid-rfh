from opal.core.test import OpalTestCase
from elcid import Application
from apps.tb import constants as tb_constants


class ApplicationTestCase(OpalTestCase):
    def setUp(self):
        super(ApplicationTestCase, self).setUp()
        self.user.is_superuser = False
        self.user.save()

    def test_get_menu_items_superuser(self):
        self.user.is_superuser = True
        self.user.save()
        menu_items = Application.get_menu_items(self.user)
        expected_hrefs = [menu_item.href for menu_item in menu_items]
        self.assertIn("/pathway/#/add_patient", expected_hrefs)

    def test_get_menu_items_tb(self):
        self.user.profile.roles.create(
            name=tb_constants.TB_ROLE
        )
        menu_items = Application.get_menu_items(self.user)
        expected_hrefs = [menu_item.href for menu_item in menu_items]
        self.assertNotIn("/pathway/#/add_patient", expected_hrefs)

    def test_get_menu_items_not_tb(self):
        self.user.profile.roles.create(
            name=tb_constants.TB_ROLE
        ).delete()
        menu_items = Application.get_menu_items(self.user)
        expected_hrefs = [menu_item.href for menu_item in menu_items]
        self.assertIn("/pathway/#/add_patient", expected_hrefs)

    def test_make_sure_we_dont_change_a_global_object(self):
        # make sure we don't change the list as it appears on
        # the application object
        menu_items_1 = Application.get_menu_items(self.user)
        menu_items_2 = Application.get_menu_items(self.user)
        self.assertEqual(menu_items_1, menu_items_2)

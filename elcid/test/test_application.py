from django.contrib.auth.models import User
from opal.core.test import OpalTestCase
from opal import models as opal_models
from elcid import Application
from apps.tb import constants as tb_constants


class ApplicationTestCase(OpalTestCase):
    PASSWORD = "password"

    def setUp(self):
        super(ApplicationTestCase, self).setUp()
        normal_user = User.objects.create(username="normal")
        normal_user.set_password(self.PASSWORD)
        normal_user.save()
        self.normal_user = normal_user

        tb_user = User.objects.create(username="tb")
        tb_user.set_password(self.PASSWORD)
        tb_user.save()
        tb_user.profile.roles.create(
            name=tb_constants.TB_ROLE
        )
        self.tb_user = tb_user

        super_user = User.objects.create(username="super")
        super_user.set_password(self.PASSWORD)
        super_user.is_superuser = True
        super_user.save()

        self.super_user = super_user

    def test_get_menu_items_superuser(self):
        menu_items = Application.get_menu_items(self.super_user)
        expected_hrefs = [menu_item.href for menu_item in menu_items]
        self.assertIn("/pathway/#/add_patient", expected_hrefs)
        self.assertIn("/#/list/", expected_hrefs)

    def test_get_menu_items_for_tb_user(self):
        menu_items = Application.get_menu_items(self.tb_user)
        expected_hrefs = [menu_item.href for menu_item in menu_items]
        self.assertNotIn("/pathway/#/add_patient", expected_hrefs)
        self.assertNotIn("/#/list/", expected_hrefs)

    def test_get_menu_items_for_normal_user(self):
        menu_items = Application.get_menu_items(self.normal_user)
        expected_hrefs = [menu_item.href for menu_item in menu_items]
        self.assertIn("/pathway/#/add_patient", expected_hrefs)
        self.assertIn("/#/list/", expected_hrefs)

    def test_make_sure_we_dont_change_a_global_object(self):
        # make sure we don't change the list as it appears on
        # the application object
        menu_items_1 = Application.get_menu_items(self.user)
        menu_items_2 = Application.get_menu_items(self.user)
        self.assertEqual(menu_items_1, menu_items_2)

from opal.core.test import OpalTestCase
from apps.tb import constants as tb_constants
from apps.tb import plugin


class MenuItemsTestCase(OpalTestCase):
    def setUp(self):
        super(MenuItemsTestCase, self).setUp()
        self.user.is_superuser = False
        self.user.save()

    def test_menu_items_super_user(self):
        self.user.is_superuser = True
        self.user.save()

        items = plugin.TbPlugin.get_menu_items(self.user)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(
            item.href, '/pathway/#/add_tb_patient'
        )
        self.assertEqual(
            item.display, 'Add TB Patient'
        )

    def test_menu_items_tb(self):
        self.user.profile.roles.create(
            name=tb_constants.TB_ROLE
        )

        items = plugin.TbPlugin.get_menu_items(self.user)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(
            item.href, '/pathway/#/add_tb_patient'
        )
        self.assertEqual(
            item.display, 'Add Patient'
        )

    def test_menu_items_no_tb(self):
        self.user.profile.roles.filter(
            name=tb_constants.TB_ROLE
        ).delete()
        items = plugin.TbPlugin.get_menu_items(self.user)
        self.assertEqual(len(items), 0)

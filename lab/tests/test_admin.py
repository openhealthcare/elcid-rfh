from opal.core.test import OpalTestCase
from unittest import mock
from lab import admin
from lab.tests import models as test_models
from lab import models


@mock.patch('lab.admin.admin')
@mock.patch('lab.admin.LabTest.list')
class adminTestCase(OpalTestCase):
    def test_register(self, lab_test_list, admin_mock):
        lab_test_list.return_value = [test_models.SomeGenericTest]
        admin.register_lab_tests()
        call_args = admin_mock.site.register.call_args_list
        self.assertEqual(
            call_args[0][0], (test_models.SomeGenericTest, admin.LabTestAdmin,)
        )
        self.assertEqual(
            call_args[1][0],
            (models.Observation, admin.LabTestAdmin,)
        )

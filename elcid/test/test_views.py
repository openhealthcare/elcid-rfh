"""
Unittests for the UCLH eLCID OPAL implementation.
"""
from django.contrib.auth.models import User
from django.urls import reverse
import ffs

from opal.core.test import OpalTestCase
from opal.models import Patient
from opal.core.subrecords import subrecords

from elcid import views


HERE = ffs.Path.here()
TEST_DATA = HERE/'test_data'


class ViewsTest(OpalTestCase):
    fixtures = ['patients_users', 'patients_options', 'patients_records']

    def setUp(self):
        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.PASSWORD))
        self.patient = Patient.objects.get(pk=1)

    def test_try_to_update_nonexistent_demographics_subrecord(self):
        response = self.put_json('/api/v0.1/demographics/1234/', {})
        self.assertEqual(404, response.status_code)

    def test_episode_list_template_view(self):
        self.assertStatusCode('/templates/patient_list.html/team_1', 200)

    def test_episode_detail_template_view(self):
        self.assertStatusCode('/templates/episode_detail.html/1', 200)

    def test_add_patient_template_view(self):
        self.assertStatusCode('/templates/modals/add_episode.html/', 200)

    def test_delete_item_confirmation_template_view(self):
        self.assertStatusCode('/templates/delete_item_confirmation_modal.html/', 200)

    def test_all_modal_templates(self):
        """ This renders all of our modal templates and blows up
            if they fail to render
        """
        for i in subrecords():
            if i.get_form_template():
                url = reverse("{}_modal".format(i.get_api_name()))
                self.assertStatusCode(url, 200)


class DetailSchemaViewTest(OpalTestCase):
    fixtures = ['patients_users', 'patients_options', 'patients_records']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.assertTrue(self.client.login(username=self.user.username,
                                          password='password'))
        self.patient = Patient.objects.get(pk=1)
        schema_file = TEST_DATA/'detail.schema.json'
        self.schema = schema_file.json_load()

    def assertStatusCode(self, path, expected_status_code):
        response = self.client.get(path)
        self.assertEqual(expected_status_code, response.status_code)


class ExtractSchemaViewTest(OpalTestCase):
    fixtures = ['patients_users', 'patients_options', 'patients_records']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.assertTrue(self.client.login(username=self.user.username,
                                          password='password'))
        self.patient = Patient.objects.get(pk=1)
        schema_file = TEST_DATA/'extract.schema.json'
        self.schema = schema_file.json_load()

    def assertStatusCode(self, path, expected_status_code):
        response = self.client.get(path)
        self.assertEqual(expected_status_code, response.status_code)


class WardSortTestCase(OpalTestCase):
    def test_ward_sort(self):
        wards = [
            "8 West",
            "PITU",
            "ICU 4 East",
            "9 East",
            "8 South",
            "9 North",
            "ICU 4 West",
            "12 West",
            "Outpatients",
        ]

        expected = [
            "8 South",
            "8 West",
            "9 East",
            "9 North",
            "12 West",
            "ICU 4 East",
            "ICU 4 West",
            "Outpatients",
            "PITU",
        ]
        self.assertEqual(
            expected, sorted(wards, key=views.ward_sort_key)
        )

    def test_grouping(self):
        wards = [
            "8 West",
            "8 West",
            "9 East",
            "8 South",
            "9 North",
        ]

        expected = [
            "8 South",
            "8 West",
            "8 West",
            "9 East",
            "9 North",
        ]
        self.assertEqual(
            expected, sorted(wards, key=views.ward_sort_key)
        )

    def test_numerical_ordering(self):
        wards = [
            "10 North",
            "10 East",
            "11 West",
            "8 North",
            "5 South",
        ]

        expected = [
            "5 South",
            "8 North",
            "10 East",
            "10 North",
            "11 West",
        ]
        self.assertEqual(
            expected, sorted(wards, key=views.ward_sort_key)
        )

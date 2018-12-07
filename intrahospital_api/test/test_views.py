import mock

from django.contrib.auth.models import User
from django.urls import reverse

from opal.core.test import OpalTestCase
from opal.models import UserProfile

from intrahospital_api import views


class BaseViewTestcase(OpalTestCase):
    def setUp(self):
        self.raw_url = reverse(
            "raw_view", kwargs=dict(hospital_number="123132123")
        )

        self.cooked_url = reverse(
            "cooked_view", kwargs=dict(hospital_number="123132123")
        )
        user = User.objects.create(
            username="Wilma",
            is_staff=True
        )

        user.set_password("fake")
        user.save()

        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            can_extract=True
        )
        self.assertTrue(
            self.client.login(
                username="Wilma", password="fake"
            )
        )


class StaffRequiredTest(BaseViewTestcase):
    def test_intrahospital_raw_view(self):
        response = self.client.get(self.raw_url)
        self.assertEqual(response.status_code, 200)

    def test_intrahospital_cooked_view(self):
        response = self.client.get(self.raw_url)
        self.assertEqual(response.status_code, 200)


class NoneStaffRequiredTest(BaseViewTestcase):
    def setUp(self):
        super(NoneStaffRequiredTest, self).setUp()
        User.objects.filter(username="Wilma").update(is_staff=False)

    def test_intrahospital_raw_view(self):
        response = self.client.get(self.raw_url, follow=True)
        expected = [(
            '/admin/login/?next=/intrahospital_api/raw/patient/123132123', 302
        )]
        self.assertEqual(expected, response.redirect_chain)

    def test_intrahospital_cooked_view(self):
        response = self.client.get(self.raw_url, follow=True)
        expected = [(
            '/admin/login/?next=/intrahospital_api/raw/patient/123132123', 302
        )]
        self.assertEqual(expected, response.redirect_chain)


class PivotTestCase(BaseViewTestcase):
    def setup_view(self, view, url, hospital_number):
        v = view()
        v.request = self.rf.get(url)
        v.kwargs = dict(hospital_number=hospital_number)
        return v

    @mock.patch("intrahospital_api.views.get_api")
    def test_intrahospital_raw_view(self, get_api):
        get_api().raw_data.return_value = [
            dict(name="Wilma"),
            dict(name="Betty"),
        ]
        view = self.setup_view(
            views.IntrahospitalRawView, self.raw_url, "123132123"
        )
        ctx = view.get_context_data(hospital_number="123132123")
        self.assertEqual(ctx["title"], "All Raw Data")
        self.assertEqual(
            ctx["row_data"], [['name', 'Wilma', 'Betty']]
        )

    @mock.patch("intrahospital_api.views.get_api")
    def test_intrahospital_cooked_view(self, get_api):
        get_api().cooked_data.return_value = [
            dict(name="Wilma"),
            dict(name="Betty"),
        ]
        view = self.setup_view(
            views.IntrahospitalCookedView, self.cooked_url, "123132123"
        )
        ctx = view.get_context_data(hospital_number="123132123")
        self.assertEqual(ctx["title"], "All Cooked Data")
        self.assertEqual(
            ctx["row_data"], [['name', 'Wilma', 'Betty']]
        )

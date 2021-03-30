from opal.core.test import OpalTestCase
from django.urls import reverse


class ViewsTestCase(OpalTestCase):
    def setUp(self):
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )

    def test_get_lab_sync_dashboard(self):
        url = reverse("lab_sync_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_lab_timings(self):
        url = reverse("system_stats_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

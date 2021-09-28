from opal.core.test import OpalTestCase
from rest_framework.reverse import reverse
from plugins.labtests import models as lab_models


class StarObservationTestCase(OpalTestCase):
    def setUp(self):
        self.request = self.rf.get("/")
        self.list_url = reverse(
            "lab_test_results_view-list",
            request=self.request
        )
        # initialise the property
        self.user
        self.assertTrue(
            self.client.login(
                username=self.USERNAME,
                password=self.PASSWORD
            )
        )
        self.patient, _ = self.new_patient_and_episode_please()
        return super().setUp()

    def test_create(self):
        self.client.post(self.list_url, {
            "patient_id": self.patient.id,
            "test_name": "Blood culture",
            "lab_number": "111",
            "observation_name": "Culture result",
        })
        self.assertTrue(
            lab_models.StarredObservsation.objects.filter(
                patient_id=self.patient.id,
                test_name="Blood culture",
                lab_number="111",
                observation_name="Culture result",
                created_by=self.user
            ).exists()
        )
        self.assertEqual(lab_models.StarredObservsation.objects.count(), 1)

    def test_delete(self):
        starred_obs = lab_models.StarredObservsation.objects.create(
            patient_id=self.patient.id,
            test_name="Blood culture",
            lab_number="111",
            observation_name="Culture result",
            created_by=self.user
        )
        detail_url = reverse(
            "lab_test_results_view-detail",
            kwargs={'pk': starred_obs.id},
            request=self.request,
        )
        self.client.delete(detail_url)
        self.assertFalse(
            lab_models.StarredObservsation.objects.all().exists()
        )

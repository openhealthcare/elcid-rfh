import mock
from django.test import RequestFactory
from django.core.urlresolvers import reverse
from opal.core.patient_lists import PatientList
from rest_framework.reverse import reverse as drf_reverse
from opal.core.test import OpalTestCase
from opal.models import Patient, Episode
from lab import models as lmodels


class TestPatientList(OpalTestCase):
    def setUp(self):
        self.patient = Patient.objects.create()
        self.episode_1 = self.patient.create_episode()
        self.episode_2 = self.patient.create_episode()
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        self.factory = RequestFactory()

    def test_get_all_patient_lists(self):
        # this should not be taken as a reason not to do more indepth unit tests!
        # its just a nice sanity check
        patient_lists = PatientList.list()
        for pl in patient_lists:
            slug = pl.get_slug()
            url = reverse(
                "patient_list_template_view", kwargs={"slug": slug}
            )

            self.assertStatusCode(
                url, 200,
                msg="Failed to load the template for {}".format(slug)
            )

    def test_get_all_patient_api(self):
        # this should not be taken as a reason not to do more indepth unit tests!
        # its just a nice sanity check
        patient_lists = PatientList.list()
        request = self.factory.get("/")
        request.user = self.user
        for pl in patient_lists:
            slug = pl.get_slug()
            url = drf_reverse(
                "patientlist-detail", kwargs={"pk": slug}, request=request
            )

            self.assertStatusCode(
                url, 200,
                msg="Failed to load the template for {}".format(slug)
            )

    def test_patient_list_episode_comparators(self):
        patient_lists = PatientList.list()
        self.assertTrue(all(i.comparator_service for i in patient_lists))

    @mock.patch("elcid.patient_lists.RfhPatientList.get_queryset")
    def test_patient_list_to_dict(self, get_queryset):
        lmodels.LabTest.objects.create(patient=self.patient)
        pl_cls = PatientList.list()[0]
        pl = pl_cls()
        get_queryset.return_value = Episode.objects.all()
        as_dict = pl.to_dict(self.user)
        self.assertNotIn("lab_test", as_dict)
        previous = Episode.objects.serialised(
            self.user, Episode.objects.all()
        )
        for i in previous:
            del i["lab_test"]
        self.assertEqual(as_dict, previous)

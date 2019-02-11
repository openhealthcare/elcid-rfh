import datetime
import json

from django.test import RequestFactory
from django.core.urlresolvers import reverse
from rest_framework.reverse import reverse as drf_reverse

from opal.core.patient_lists import PatientList
from opal.core.test import OpalTestCase
from opal.models import Patient

from elcid import models
from elcid.patient_lists import RfhPatientList


class AbstractPatientListTestCase(OpalTestCase):
    def create_episode(self):
        patient, episode = self.new_patient_and_episode_please()
        primary_diagnosis = episode.primarydiagnosis_set.get()
        primary_diagnosis.condition = "cough"
        primary_diagnosis.save()
        antimicrobial = models.Antimicrobial.objects.create(episode=episode)
        antimicrobial.drug = "Aspirin"
        antimicrobial.save()
        diagnosis = models.Diagnosis.objects.create(episode=episode)
        diagnosis.condition = "fever"
        diagnosis.save()
        demographics = patient.demographics_set.get()
        demographics.first_name = "Wilma"
        demographics.surname = "Flintstone"
        demographics.save()
        gram_stain = models.GramStain.objects.create(
            datetime_ordered=datetime.datetime.now(),
            patient=patient,
        )

        gram_stain.extras = dict(
            lab_number="212",
            aerobic=False,
            isolate=1
        )
        gram_stain.save()
        return episode


class TestPatientList(AbstractPatientListTestCase):
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
        pls = PatientList.list()
        for pl in pls:
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
        pls = PatientList.list()
        request = self.factory.get("/")
        request.user = self.user
        for pl in pls:
            slug = pl.get_slug()
            url = drf_reverse(
                "patientlist-detail", kwargs={"pk": slug}, request=request
            )

            self.assertStatusCode(
                url, 200,
                msg="Failed to load the template for {}".format(slug)
            )

    def test_get(self):
        episode = self.create_episode()
        pls = PatientList.list()
        pl = list(pls)[0]
        episode.set_tag_names([pl.tag], self.user)

        request = self.factory.get("/")
        request.user = self.user
        slug = pl.get_slug()
        url = drf_reverse(
            "patientlist-detail", kwargs={"pk": slug}, request=request
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        contents = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(contents), 1)
        episode_serialised = contents[0]

        self.assertNotIn("lab_tests", episode_serialised)

        self.assertEqual(
            episode_serialised["diagnosis"][0]["condition"], "fever"
        )

        self.assertEqual(
            episode_serialised["demographics"][0]["first_name"], "Wilma"
        )

        self.assertEqual(
            episode_serialised["primary_diagnosis"][0]["condition"], "cough"
        )

        self.assertEqual(
            episode_serialised["antimicrobial"][0]["drug"], "Aspirin"
        )

    def test_patient_list_episode_comparators(self):
        pls = PatientList.list()
        self.assertTrue(all(
            i.comparator_service for i in pls if issubclass(i, RfhPatientList)
        ))

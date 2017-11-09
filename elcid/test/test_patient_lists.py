import datetime
import json

from django.test import RequestFactory
from django.core.urlresolvers import reverse
from rest_framework.reverse import reverse as drf_reverse

from opal.core.patient_lists import PatientList
from opal.core.test import OpalTestCase
from opal.models import Patient, Tagging, Episode

from elcid import models
from elcid import patient_lists


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
            date_ordered=datetime.date.today(),
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
        contents = json.loads(response.content)
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
        self.assertTrue(all(i.comparator_service for i in pls))


class SerialisedTestCase(AbstractPatientListTestCase):
    def test_serialised_only_serialises_relevent_subrecords(self):
        subrecords = [
            models.PrimaryDiagnosis,
            models.Demographics,
            models.Antimicrobial,
            models.Diagnosis,
            Tagging
        ]
        episode = self.create_episode()
        episode.set_tag_names(['something'], self.user)
        episodes = Episode.objects.all()
        serialised = patient_lists.serialised(
            episodes, self.user, subrecords=subrecords
        )

        expected_keys = (i.get_api_name() for i in subrecords)

        for expected_key in expected_keys:
            self.assertIn(expected_key, serialised[0])

        self.assertNotIn(models.Location.get_api_name(), serialised[0])

    def test_serialised_historic_tags_true(self):
        _, episode = self.new_patient_and_episode_please()
        episode.set_tag_names(['something'], self.user)
        episode.set_tag_names(['else'], self.user)
        episodes = Episode.objects.all()
        serialised = patient_lists.serialised(
            episodes, self.user, subrecords=[Tagging], historic_tags=True
        )
        self.assertEqual(
            serialised[0]["tagging"],
            [{"id": 1, "something": True, "else": True}]
        )

    def test_serialised_historic_tags_default(self):
        _, episode = self.new_patient_and_episode_please()
        episode.set_tag_names(['something'], self.user)
        episode.set_tag_names(['else'], self.user)
        episodes = Episode.objects.all()
        serialised = patient_lists.serialised(
            episodes, self.user, subrecords=[Tagging]
        )
        self.assertEqual(
            serialised[0]["tagging"],
            [{"id": 1, "else": True}]
        )

    def test_patient_subrecords(self):
        episode = self.create_episode()
        episode.set_tag_names(['something'], self.user)
        episodes = Episode.objects.all()

        serialised = patient_lists.serialised_patient_subrecords(
            episodes, self.user, subrecords=[
                models.Demographics,
                models.Diagnosis,
                Tagging
            ]
        )

        s = serialised.values()[0]

        self.assertIn(models.Demographics.get_api_name(), s)
        self.assertNotIn(Tagging.get_api_name(), s)
        self.assertNotIn(models.Diagnosis.get_api_name(), s)
        self.assertEqual(
            s[models.Demographics.get_api_name()][0]["first_name"], "Wilma"
        )

    def test_episode_subrecords(self):
        episode = self.create_episode()
        episode.set_tag_names(['something'], self.user)
        episodes = Episode.objects.all()

        serialised = patient_lists.serialised_episode_subrecords(
            episodes, self.user, subrecords=[
                models.Demographics,
                models.Diagnosis,
                Tagging
            ]
        )

        s = serialised.values()[0]

        self.assertIn(models.Diagnosis.get_api_name(), s)
        self.assertNotIn(models.Demographics.get_api_name(), s)
        self.assertNotIn(Tagging.get_api_name(), s)
        self.assertEqual(
            s[models.Diagnosis.get_api_name()][0]["condition"], "fever"
        )

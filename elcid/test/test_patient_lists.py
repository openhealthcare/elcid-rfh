import datetime
import json
from unittest import mock

from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from rest_framework.reverse import reverse as drf_reverse

from opal.core.patient_lists import PatientList
from opal.core.test import OpalTestCase
from opal.models import Patient

from elcid import models
from elcid import episode_categories
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
        self.assertEqual(
            patient_lists.Hepatology.comparator_service,
            "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.SurgicalAntibioti.comparator_service,
            "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.MAU.comparator_service, "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.Antifungal.comparator_service,
            "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.RnohWardround.comparator_service,
            "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.CDIFF.comparator_service, "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.ICU.comparator_service, "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.Acute.comparator_service, "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.Chronic.comparator_service, "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.Haematology.comparator_service,
            "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.HIV.comparator_service, "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.MalboroughClinic.comparator_service,
            "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.Renal.comparator_service, "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.Sepsis.comparator_service, "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.PCP.comparator_service, "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.R1.comparator_service, "EpisodeAddedComparator"
        )
        self.assertEqual(
            patient_lists.LiverTransplantation.comparator_service,
            "EpisodeAddedComparator"
        )

        self.assertEqual(
            patient_lists.ChronicAntifungal.comparator_service,
            "EpisodeAddedComparator"
        )


class ChronicAntifungalTestCase(OpalTestCase):
    def setUp(self):
        self.patient, self.episode = self.new_patient_and_episode_please()
        category_name = episode_categories.InfectionService.display_name
        self.episode.category_name = category_name
        self.episode.save()
        self.patient_list = patient_lists.ChronicAntifungal()
        self.now = timezone.now()

    @mock.patch('django.utils.timezone.now')
    def test_includes_new_chronic_antifungal(self, now):
        now.return_value = self.now - datetime.timedelta(3)
        self.patient.chronicantifungal_set.create(
            reason=models.ChronicAntifungal.DISPENSARY_REPORT
        )
        self.assertEqual(list(self.patient_list.queryset), [self.episode])

    @mock.patch('django.utils.timezone.now')
    def test_includes_multiple_new_chronic_antifungal(self, now):
        now.return_value = self.now - datetime.timedelta(3)
        self.patient.chronicantifungal_set.create(
            reason=models.ChronicAntifungal.DISPENSARY_REPORT
        )
        self.patient.chronicantifungal_set.create(
            reason=models.ChronicAntifungal.DISPENSARY_REPORT
        )
        self.assertEqual(list(self.patient_list.queryset), [self.episode])

    @mock.patch('django.utils.timezone.now')
    def test_excludes_old_chronic_antifungal(self, now):
        now.return_value = self.now - datetime.timedelta(4)
        self.patient.chronicantifungal_set.create(
            reason=models.ChronicAntifungal.DISPENSARY_REPORT
        )
        self.assertEqual(list(self.patient_list.queryset), [])

    def test_excludes_chrnoic_antifungal_is_none(self):
        self.assertEqual(list(self.patient_list.queryset), [])

    def test_returns_most_recent_episode_if_multiple_are_available(self):
        episode_2 = self.patient.create_episode()
        self.patient.chronicantifungal_set.create(
            reason=models.ChronicAntifungal.DISPENSARY_REPORT
        )
        self.assertEqual(list(self.patient_list.queryset), [episode_2])

    def test_ignores_episodes_of_other_categories(self):
        self.episode.category_name = "TB"
        self.episode.save()
        self.patient.chronicantifungal_set.create(
            reason=models.ChronicAntifungal.DISPENSARY_REPORT
        )
        self.assertEqual(list(self.patient_list.queryset), [])


class OrganismPatientlistTestCase(OpalTestCase):
    def setUp(self):
        self.patient, self.episode = self.new_patient_and_episode_please()
        self.patient_list = patient_lists.OrganismPatientlist()

    def test_four_months_ago(self):
        before = timezone.make_aware(datetime.datetime(
            2019, 8, 1
        ))
        with mock.patch(
            "elcid.patient_lists.timezone.now"
        ) as timezone_now:
            timezone_now.return_value = before
            self.assertEqual(
                self.patient_list.four_months_ago(),
                timezone.make_aware(
                    datetime.datetime(
                        2019, 4, 3
                    )
                )
            )

    def test_get_observations_only_includes_blood_cultures(self):
        lab_test_1 = self.patient.lab_tests.create(
            test_name="BLOOD CULTURE",
            datetime_ordered=timezone.now(),
            patient=self.patient
        )
        observation = lab_test_1.observation_set.create(
            observation_name="Blood Culture",
        )
        patient2, _ = self.new_patient_and_episode_please()
        lab_test_2 = patient2.lab_tests.create(
            test_name="NOT BLOOD CULTURE",
            datetime_ordered=timezone.now(),
            patient=self.patient
        )
        lab_test_2.observation_set.create(
            observation_name="Blood Culture",
        )

        patient3, _ = self.new_patient_and_episode_please()
        lab_test_3 = patient2.lab_tests.create(
            test_name="BLOOD CULTURE",
            datetime_ordered=timezone.now(),
            patient=self.patient
        )
        lab_test_3.observation_set.create(
            observation_name="Not Blood Culture",
        )
        self.assertEqual(
            self.patient_list.get_observations().get().id,
            observation.id
        )

    def test_queryset(self):
        lab_test = self.patient.lab_tests.create(
            test_name="BLOOD CULTURE",
            datetime_ordered=timezone.now(),
            patient=self.patient
        )
        lab_test.observation_set.create(
            observation_name="Blood Culture",
        )
        self.assertEqual(
            self.patient_list.queryset.get().id,
            self.episode.id
        )

    def test_queryset_distinct(self):
        lab_test = self.patient.lab_tests.create(
            test_name="BLOOD CULTURE",
            datetime_ordered=timezone.now(),
            patient=self.patient
        )
        lab_test.observation_set.create(
            observation_name="Blood Culture",
        )
        lab_test.observation_set.create(
            observation_name="Blood Culture",
        )
        self.assertEqual(
            self.patient_list.queryset.get().id,
            self.episode.id
        )


class CandidaTestCase(OpalTestCase):
    def setUp(self):
        self.patient, self.episode = self.new_patient_and_episode_please()
        self.patient_list = patient_lists.CandidaList()

    def test_get_queryset_includes_candida(self):
        lab_test = self.patient.lab_tests.create(
            test_name="BLOOD CULTURE",
            datetime_ordered=timezone.now(),
            patient=self.patient
        )
        lab_test.observation_set.create(
            observation_name="Blood Culture",
            observation_value="candida"
        )
        self.assertEqual(
            self.patient_list.queryset.get().id,
            self.episode.id
        )

    def test_get_queryset_excludes_candida(self):
        lab_test = self.patient.lab_tests.create(
            test_name="BLOOD CULTURE",
            datetime_ordered=timezone.now(),
            patient=self.patient
        )
        lab_test.observation_set.create(
            observation_name="Blood Culture",
            observation_value="something else"
        )
        self.assertFalse(self.patient_list.queryset.exists())

    def test_get_queryset_ignores_strings(self):
        lab_test = self.patient.lab_tests.create(
            test_name="BLOOD CULTURE",
            datetime_ordered=timezone.now(),
            patient=self.patient
        )
        lab_test.observation_set.create(
            observation_name="Blood Culture",
            observation_value="Candida NOT isolatede"
        )
        self.assertFalse(self.patient_list.queryset.exists())


class StaphAureusListListTestCase(OpalTestCase):
    def setUp(self):
        self.patient, self.episode = self.new_patient_and_episode_please()
        self.patient_list = patient_lists.StaphAureusList()

    def test_get_queryset_includes_staph(self):
        lab_test = self.patient.lab_tests.create(
            test_name="BLOOD CULTURE",
            datetime_ordered=timezone.now(),
            patient=self.patient
        )
        lab_test.observation_set.create(
            observation_name="Blood Culture",
            observation_value="1) Staphylococcus aureus"
        )
        self.assertEqual(
            self.patient_list.queryset.get().id,
            self.episode.id
        )

    def test_get_queryset_excludes_not_staph_aureus(self):
        lab_test = self.patient.lab_tests.create(
            test_name="BLOOD CULTURE",
            datetime_ordered=timezone.now(),
            patient=self.patient
        )
        lab_test.observation_set.create(
            observation_name="Blood Culture",
            observation_value="Staphylococcus hominis"
        )
        self.assertFalse(self.patient_list.queryset.exists())

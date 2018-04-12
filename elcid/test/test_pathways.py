from datetime import date
from mock import patch
from django.test import override_settings
from django.contrib.auth.models import User
from intrahospital_api import constants

from opal import models
from opal.core.test import OpalTestCase
from elcid.pathways import (
    AddPatientPathway, CernerDemoPathway, BloodCulturePathway,
    IgnoreDemographicsMixin
)
from elcid import models as emodels


@override_settings(
    ASYNC_API=False,
    INTRAHOSPITAL_API='intrahospital_api.apis.dev_api.DevApi',
    API_USER="ohc"
)
class PathwayTestCase(OpalTestCase):
    def setUp(self):
        super(PathwayTestCase, self).setUp()
        User.objects.create(username="ohc", password="fake_password")


class IgnoreDemographicsMixinTestCase(PathwayTestCase):
    def setUp(self):
        class SomeSaveParentPathway(object):
            def save(self, data, user=None, episode=None, patient=None):
                self.data = data
                self.user = user
                self.episode = episode
                self.patient = patient

        class SomeSaveChildPathway(
            IgnoreDemographicsMixin, SomeSaveParentPathway
        ):
            pass

        self.pathway = SomeSaveChildPathway()
        self.patient, self.episode = self.new_patient_and_episode_please()

    def test_popped_with_external_system(self):
        self.patient.demographics_set.update(
            first_name="Paul",
            surname="Daniels",
            external_system=constants.EXTERNAL_SYSTEM
        )
        data = dict(demographics=[{"first_name": "Daniel"}])
        self.pathway.save(
            data, user=self.user, episode=self.episode, patient=self.patient
        )

        self.assertEqual(
            self.pathway.user, self.user
        )
        self.assertEqual(
            self.pathway.episode, self.episode
        )
        self.assertEqual(
            self.pathway.patient, self.patient
        )
        self.assertEqual(
            self.pathway.data, {}
        )

    def test_popped_without_external_system(self):
        self.patient.demographics_set.update(
            first_name="Paul",
            surname="Daniels",
        )
        data = dict(demographics=[{"first_name": "Daniel"}])
        self.pathway.save(
            data, user=self.user, episode=self.episode, patient=self.patient
        )

        self.assertEqual(
            self.pathway.user, self.user
        )
        self.assertEqual(
            self.pathway.episode, self.episode
        )
        self.assertEqual(
            self.pathway.patient, self.patient
        )
        self.assertEqual(
            self.pathway.data, dict(demographics=[{"first_name": "Daniel"}])
        )


class BloodCulturePathwayTestCase(PathwayTestCase):
    def test_includes_demographcis_with_external_system(self):
        patient, episode = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name="Paul",
            surname="Daniels",
        )

        quick_fish = patient.labtest_set.create(
            lab_test_type='QuickFISH',
        )
        data = dict(
            lab_test=[{
                "id": quick_fish.id,
                "lab_test_type": "QuickFISH",
                "result": {"result": "CNS"}
            }],
            demographics=[{
                "first_name": "Daniel",
                "surname": "Pauls",
            }]
        )
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        pathway = BloodCulturePathway()
        url = pathway.save_url(patient=patient, episode=episode)
        result = self.post_json(url, data)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            patient.demographics_set.first().first_name,
            "Daniel"
        )

    def test_ignores_demographics_with_external_system(self):
        patient, episode = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name="Paul",
            surname="Daniels",
            external_system=constants.EXTERNAL_SYSTEM,
            external_identifier="blah"
        )

        quick_fish = patient.labtest_set.create(
            lab_test_type='QuickFISH',
        )
        data = dict(
            lab_test=[{
                "id": quick_fish.id,
                "lab_test_type": "QuickFISH",
                "result": {"result": "CNS"}
            }],
            demographics=[{
                "first_name": "Daniel",
                "surname": "Pauls",
            }]
        )
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        pathway = BloodCulturePathway()
        url = pathway.save_url(patient=patient, episode=episode)
        result = self.post_json(url, data)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            patient.demographics_set.first().first_name,
            "Paul"
        )

    def test_delete_others(self):
        # in theory this should just work, but lets
        # double check the underlying api hasn't changed
        patient, episode = self.new_patient_and_episode_please()
        patient.labtest_set.create(
            lab_test_type='Gram Stain',
        )
        quick_fish = patient.labtest_set.create(
            lab_test_type='QuickFISH',
        )
        data = dict(
            lab_test=[{
                "id": quick_fish.id,
                "lab_test_type": "QuickFISH",
                "result": {"result": "CNS"}
            }]
        )
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        pathway = BloodCulturePathway()
        url = pathway.save_url(patient=patient, episode=episode)
        result = self.post_json(url, data)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            patient.labtest_set.get().lab_test_type, "QuickFISH"
        )

    def test_delete_others_ignores_upstream_tests(self):
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        patient, episode = self.new_patient_and_episode_please()
        patient.labtest_set.create(
            lab_test_type='Gram Stain',
        )
        quick_fish = patient.labtest_set.create(
            lab_test_type='QuickFISH',
        )
        upstream_lab_test = patient.labtest_set.create(
            lab_test_type=emodels.UpstreamLabTest.get_display_name(),
            external_system=constants.EXTERNAL_SYSTEM
        )
        upstream_blood_culture = patient.labtest_set.create(
            lab_test_type=emodels.UpstreamBloodCulture.get_display_name(),
            external_system=constants.EXTERNAL_SYSTEM
        )

        data = dict(
            lab_test=[{
                "id": quick_fish.id,
                "lab_test_type": "QuickFISH",
                "result": {"result": "CNS"}
            }]
        )

        pathway = BloodCulturePathway()
        url = pathway.save_url(patient=patient, episode=episode)
        result = self.post_json(url, data)
        self.assertEqual(result.status_code, 200)
        expected_quick_fish = patient.labtest_set.first()
        self.assertEqual(
            expected_quick_fish.id, quick_fish.id
        )
        self.assertEqual(
            expected_quick_fish.lab_test_type, quick_fish.lab_test_type
        )

        expected_upstream_lab_test = patient.labtest_set.all()[1]
        self.assertEqual(
            expected_upstream_lab_test.id, upstream_lab_test.id
        )
        self.assertEqual(
            expected_upstream_lab_test.lab_test_type,
            upstream_lab_test.lab_test_type
        )

        expected_upstream_blood_culture = patient.labtest_set.all()[2]
        self.assertEqual(
            expected_upstream_blood_culture.id, upstream_blood_culture.id
        )
        self.assertEqual(
            expected_upstream_blood_culture.lab_test_type,
            upstream_blood_culture.lab_test_type
        )


class TestCernerDemoPathway(PathwayTestCase):
    data = dict(
        demographics=[dict(hospital_number="234", nhs_number="12312")],
        procedure=[dict(date=date.today())],
        tagging=[{u'antifungal': True}]
    )

    def setUp(self):
        super(TestCernerDemoPathway, self).setUp()

        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )

    def test_post_existing_pathway(self):
        patient, episode = self.new_patient_and_episode_please()
        patient.demographics_set.update(hospital_number="234")
        test_data = dict(
            demographics=[dict(
                hospital_number="234",
                nhs_number="12312",
                patient_id=patient.id
            )],
        )
        pathway = CernerDemoPathway()
        url = pathway.save_url(patient=patient, episode=episode)
        result = self.post_json(url, test_data)
        self.assertEqual(result.status_code, 200)
        demographics = models.Patient.objects.get().demographics_set.first()
        self.assertEqual(demographics.nhs_number, "12312")


class TestAddPatientPathway(PathwayTestCase):
    def setUp(self):
        super(TestAddPatientPathway, self).setUp()
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        self.url = AddPatientPathway().save_url()

    @patch("elcid.pathways.loader.load_patient")
    @override_settings(ADD_PATIENT_LAB_TESTS=True)
    def test_queries_loader_if_external_demographics(self, load_patient):
        test_data = dict(
            demographics=[dict(
                hospital_number="234",
                nhs_number="12312",
                external_system=constants.EXTERNAL_SYSTEM
            )],
            tagging=[{u'antifungal': True}],
        )
        response = self.post_json(self.url, test_data)
        self.assertEqual(response.status_code, 200)
        load_patient.assert_called_once_with(
            models.Patient.objects.get()
        )

    @patch("elcid.pathways.loader.load_patient")
    @override_settings(ADD_PATIENT_LAB_TESTS=True)
    def test_does_not_query_loader_if_local_demographics(
        self, load_patient
    ):
        test_data = dict(
            demographics=[dict(
                hospital_number="234",
                nhs_number="12312"
            )],
            tagging=[{u'antifungal': True}],
        )
        response = self.post_json(self.url, test_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(load_patient.called)

    def test_saves_tag(self):
        test_data = dict(
            demographics=[dict(hospital_number="234", nhs_number="12312")],
            tagging=[{u'antifungal': True}]
        )
        response = self.post_json(self.url, test_data)
        self.assertEqual(response.status_code, 200)
        patient = models.Patient.objects.get()
        self.assertEqual(
            patient.demographics_set.first().hospital_number,
            "234"
        )
        episode = patient.episode_set.get()
        self.assertEqual(
            list(episode.get_tag_names(None)),
            ["antifungal"]
        )

    def test_saves_without_tags(self):
        test_data = dict(
            demographics=[dict(hospital_number="234", nhs_number="12312")],
        )
        self.post_json(self.url, test_data)
        patient = models.Patient.objects.get()
        self.assertEqual(
            patient.demographics_set.first().hospital_number,
            "234"
        )
        episode = patient.episode_set.get()
        self.assertEqual(
            list(episode.get_tag_names(None)),
            []
        )

    @patch("elcid.pathways.datetime")
    def test_episode_start(self, datetime):
        patient, episode = self.new_patient_and_episode_please()
        datetime.date.today.return_value = date(2016, 5, 1)
        url = AddPatientPathway().save_url()
        test_data = dict(
            demographics=[dict(hospital_number="234", nhs_number="12312")],
            tagging=[{u'antifungal': True}]
        )
        self.post_json(url, test_data)
        new_episode = models.Episode.objects.last()
        self.assertEqual(new_episode.start, date(2016, 5, 1))

        self.assertEqual(
            list(new_episode.get_tag_names(None)),
            ['antifungal']
        )

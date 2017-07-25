from datetime import date
from django.test import override_settings
from mock import patch

from opal import models
from opal.core.test import OpalTestCase
from elcid.pathways import (
    AddPatientPathway, CernerDemoPathway, BloodCulturePathway
)


class TestBloodCulturePathway(OpalTestCase):
    def test_delete_others(self):
        # in theory this should just work, but lets
        # double check the underlying api hasn't changed
        patient, episode = self.new_patient_and_episode_please()
        gram_stain = patient.labtest_set.create(
            lab_test_type='Gram Stain',
        )
        patient.labtest_set.create(
            lab_test_type='QuickFISH',
        )
        data = dict(
            lab_test=[{
                "id": gram_stain.id,
                "lab_test_type": "QuickFISH"
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


class TestCernerDemoPathway(OpalTestCase):
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


class TestAddPatientPathway(OpalTestCase):
    def setUp(self):
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        self.url = AddPatientPathway().save_url()

    @override_settings(GLOSS_ENABLED=False)
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

    @override_settings(GLOSS_ENABLED=False)
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

    @override_settings(GLOSS_ENABLED=True)
    @patch("elcid.pathways.gloss_api")
    def test_gloss_interaction_when_found(self, gloss_api):
        patient, episode = self.new_patient_and_episode_please()
        demographics = patient.demographics_set.first()
        demographics.hospital_number = "234"
        demographics.first_name = "Indiana"
        demographics.save()
        gloss_api.patient_query.return_value = patient
        test_data = dict(
            demographics=[dict(hospital_number="234", nhs_number="12312")],
            tagging=[{u'antifungal': True}]
        )
        url = AddPatientPathway().save_url(patient=patient)
        self.post_json(url, test_data)
        saved_demographics = models.Patient.objects.get().demographics_set.get()

        # we don't expect demographics to have changed as these will have been
        # loaded in from gloss
        self.assertEqual(saved_demographics.first_name, "Indiana")

        # we expect a new episode to have been created on the same patient
        saved_episode = patient.episode_set.last()
        self.assertNotEqual(episode.id, saved_episode.id)
        self.assertEqual(
            list(saved_episode.get_tag_names(None)),
            ['antifungal']
        )
        self.assertEqual(gloss_api.subscribe.call_args[0][0], "234")

    @override_settings(GLOSS_ENABLED=True)
    @patch("elcid.pathways.gloss_api")
    def test_gloss_interaction_when_only_found_in_gloss(self, gloss_api):
        def side_effect(arg):
            patient, _ = self.new_patient_and_episode_please()
            demographics = patient.demographics_set.first()
            demographics.consistency_token = "1231222"
            demographics.first_name = "Sarah"
            demographics.save()
            return patient

        gloss_api.patient_query.side_effect = side_effect
        test_data = dict(
            demographics=[dict(hospital_number="234", nhs_number="12312")],
            tagging=[{u'antifungal': True}]
        )
        self.post_json(self.url, test_data)
        saved_demographics = models.Patient.objects.get().demographics_set.get()

        # if the patient isn't found, everything should just work
        self.assertEqual(saved_demographics.first_name, "Sarah")

        saved_episode = models.Episode.objects.get()
        self.assertEqual(
            list(saved_episode.get_tag_names(None)),
            ['antifungal']
        )
        self.assertEqual(gloss_api.subscribe.call_args[0][0], "234")

    @override_settings(GLOSS_ENABLED=True)
    @patch("elcid.pathways.gloss_api")
    def test_gloss_interaction_when_not_creating_a_patient(self, gloss_api):
        patient, existing_episode = self.new_patient_and_episode_please()
        url = AddPatientPathway().save_url(
            patient=patient
        )
        demographics = patient.demographics_set.first()
        demographics.hospital_number = "234"
        gloss_api.patient_query.return_value = None
        test_data = dict(
            demographics=[dict(hospital_number="234", nhs_number="12312")],
            tagging=[{u'antifungal': True}]
        )
        self.post_json(url, test_data)
        new_episode = patient.episode_set.last()
        self.assertEqual(
            list(patient.episode_set.all()),
            [existing_episode, new_episode]
        )

        self.assertEqual(
            list(new_episode.get_tag_names(None)),
            ['antifungal']
        )
        self.assertEqual(gloss_api.subscribe.call_args[0][0], "234")

    @override_settings(GLOSS_ENABLED=False)
    @patch("elcid.pathways.SaveTaggingMixin.save")
    @patch("elcid.pathways.datetime")
    def test_episode_start(self, datetime, parent_save):
        patient, episode = self.new_patient_and_episode_please()
        parent_save.return_value = (patient, episode,)
        datetime.date.today.return_value = date(2016, 5, 1)
        url = AddPatientPathway().save_url()
        test_data = dict(
            demographics=[dict(hospital_number="234", nhs_number="12312")],
            tagging=[{u'antifungal': True}]
        )
        self.post_json(url, test_data)
        patient = parent_save.call_args[1].get("patient")
        self.assertIsNotNone(patient)
        episode = parent_save.call_args[1].get("episode")
        self.assertIsNotNone(episode)
        self.assertEqual(episode.start, date(2016, 5, 1))

        # make sure we've saved it
        self.assertEqual(models.Episode.objects.last().start, date(2016, 5, 1))

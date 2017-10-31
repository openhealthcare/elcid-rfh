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
        self.assertEqual(episode.start, date(2016, 5, 1))

        # make sure we've saved it
        self.assertEqual(models.Episode.objects.last().start, date(2016, 5, 1))

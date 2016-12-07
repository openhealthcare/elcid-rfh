from datetime import date
from opal import models
from opal.core.test import OpalTestCase


class TestCernerDemoPathway(OpalTestCase):
    url = "/pathway/cernerdemo/save"
    data = dict(
        demographics=[dict(hospital_number="234", nhs_number="12312")],
        procedure=[dict(date=date.today())],
        tagging=[{u'antifungal': True}]
    )

    def setUp(self):
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )

    def test_post_new_pathway(self):
        test_data = dict(
            demographics=[dict(hospital_number="234", nhs_number="12312")],
            tagging=[{u'antifungal': True}]
        )
        self.post_json(self.url, test_data)
        demographics = models.Patient.objects.get().demographics_set.first()
        self.assertEqual(demographics.hospital_number, "234")
        tags = models.Episode.objects.get().get_tag_names(self.user)
        self.assertEqual(list(tags), ['antifungal'])

    def test_post_existing_pathway(self):
        patient, episode = self.new_patient_and_episode_please()
        test_data = dict(
            demographics=[dict(
                hospital_number="234",
                nhs_number="12312",
                patient_id=patient.id
            )],
            tagging=[{u'antifungal': True}]
        )
        url = "{0}/{1}/{2}".format(self.url, patient.id, episode.id)
        self.post_json(url, test_data)
        self.assertEqual(
            list(models.Episode.objects.get().get_tag_names(self.user)),
            ['antifungal']
        )
        demographics = models.Patient.objects.get().demographics_set.first()
        self.assertEqual(demographics.hospital_number, "234")


class TestAddPatientPathway(OpalTestCase):
    url = "/pathway/add_patient/save/"

    def setUp(self):
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )

    def test_post_pathway(self):
        test_data = dict(
            demographics=[dict(hospital_number=234, nhs_number=12312)],
            tagging=[{u'antifungal': True}]
        )
        self.post_json(self.url, test_data)

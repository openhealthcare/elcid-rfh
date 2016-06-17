from datetime import date

from opal.core.test import OpalTestCase
from elcid.models import BloodCulture


class TestPathwayPost(OpalTestCase):
    url = "/pathway/cernerdemo/save/"

    def setUp(self):
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )

    def test_post_pathway(self):
        test_data = dict(
            demographics=[dict(hospital_number=234, nhs_number=12312)],
            procedure=[dict(date=date.today())]
        )
        self.post_json(self.url, test_data)


class BloodCulturePathwayTestCase(OpalTestCase):
    def setUp(self):
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        self.patient, self.episode = self.new_patient_and_episode_please()
        self.url = "/pathway/blood_culture/save/{0}/{1}".format(
            self.patient.id, self.episode.id
        )
        self.date_ordered = date(2012, 1, 1)
        self.date_ordered_formated = "01/01/2012"
        self.date_positive = date(2012, 1, 2)
        self.date_positive_formated = "02/01/2012"
        super(BloodCulturePathwayTestCase, self).setUp()

    def get_isolate_update_dict(self, **kwargs):
        example_dict = dict(
            lab_number="1231231212",
            episode_id=self.episode.id,
            date_ordered=self.date_ordered_formated,
            date_positive=self.date_positive_formated,
            source="Left Arm",
        )
        example_dict.update(kwargs)
        return example_dict

    def test_save_existing(self):
        existing_bc = BloodCulture.objects.create(
            **self.get_isolate_update_dict(
                source="Right Arm",
                date_ordered=self.date_ordered,
                date_positive=self.date_positive
            )
        )

        BloodCulture.objects.create(
            **self.get_isolate_update_dict(
                lab_number="111111",
                date_ordered=self.date_ordered,
                date_positive=self.date_positive
            )
        )

        data = {
            BloodCulture.get_api_name(): [
                self.get_isolate_update_dict(id=existing_bc.id)
            ]
        }

        response = self.post_json(self.url, data)
        remaining_bc = BloodCulture.objects.get()
        self.assertEqual(remaining_bc.episode_id, self.episode.id)
        self.assertEqual(remaining_bc.id, existing_bc.id)
        self.assertEqual(remaining_bc.source, "Left Arm")

    def save_new(self):
        data = {
            BloodCulture.get_api_name(): [
                self.get_isolate_update_dict()
            ]
        }

        self.post_json(self.url, data)
        bc = BloodCulture.objects.get()
        self.assertEqual(bc.episode_id, self.episode.id)
        self.assertEqual(bc.source, "Left Arm")

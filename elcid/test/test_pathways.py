from datetime import date

from opal.core.test import OpalTestCase


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

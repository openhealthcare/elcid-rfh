from opal.core.test import OpalTestCase
from datetime import date


class TestPathwayGet(OpalTestCase):
    def test_get_pathway(self):
        pass


class TestPathwayPost(OpalTestCase):
    url = "/pathway/cernerdemo/save/"

    def test_post_pathway(self):
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        test_data = dict(
            demographics=[dict(hospital_number=234, nhs_number=12312)],
            procedure=[dict(date=date.today())]
        )
        self.post_json(self.url, test_data)

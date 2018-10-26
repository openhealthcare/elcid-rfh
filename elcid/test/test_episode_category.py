from opal.core.test import OpalTestCase
from elcid import episode_categories


class EpisodeCategoryTestCase(OpalTestCase):
    def test_detail_page_render(self):
        """
        A simple test that will catch any case if we declare models
        in record panels that do not exist.
        """
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        url = "/templates/{}".format(
            episode_categories.InfectionService.detail_template
        )
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 200
        )


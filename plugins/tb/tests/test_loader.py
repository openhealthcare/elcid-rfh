from unittest import mock
from opal.core.test import OpalTestCase
from opal.models import Episode, Patient
from plugins.tb import loader
from plugins.tb import episode_categories



@mock.patch("plugins.tb.loader.create_rfh_patient_from_hospital_number")
@mock.patch("plugins.tb.loader.ProdAPI")
class CreateFollowUpEpisodeTestCase(OpalTestCase):
    def test_create_patient_who_does_not_exist(
        self,
        ProdAPI,
        create_rfh_patient_from_hospital_number
    ):
        ProdAPI.return_value.execute_hospital_query.return_value = [
            {"vPatient_Number": "111"}
        ]
        loader.create_tb_episodes()
        create_rfh_patient_from_hospital_number.assert_called_once_with(
            "111", episode_categories.TbEpisode
        )

    def test_create_episode_which_does_not_exist(
        self,
        ProdAPI,
        create_rfh_patient_from_hospital_number
    ):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(hospital_number="111")
        ProdAPI.return_value.execute_hospital_query.return_value = [
            {"vPatient_Number": "111"}
        ]
        loader.create_tb_episodes()
        patient = Patient.objects.get()
        self.assertEqual(
            patient.episode_set.count(), 2
        )
        self.assertTrue(
            patient.episode_set.filter(
                category_name=episode_categories.TbEpisode.display_name
            ).exists()
        )
        demographics = patient.demographics()
        self.assertEqual(
            demographics.hospital_number, "111"
        )
        self.assertFalse(create_rfh_patient_from_hospital_number.called)

    def test_do_nothing_if_episode_exists(
        self,
        ProdAPI,
        create_rfh_patient_from_hospital_number
    ):
        ProdAPI.return_value.execute_hospital_query.return_value = [
            {"vPatient_Number": "111"}
        ]
        patient, episode = self.new_patient_and_episode_please()
        patient.demographics_set.update(hospital_number="111")
        episode.category_name = episode_categories.TbEpisode.display_name
        episode.save()
        loader.create_tb_episodes()

        covid_episode = Episode.objects.get(
            category_name=episode_categories.TbEpisode.display_name
        )
        self.assertEqual(
            covid_episode.patient.demographics().hospital_number,
            "111"
        )
        self.assertEqual(
            Episode.objects.count(), 1
        )
        self.assertEqual(
            Patient.objects.count(), 1
        )
        self.assertFalse(create_rfh_patient_from_hospital_number.called)

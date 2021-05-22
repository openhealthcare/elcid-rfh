import datetime
from unittest import mock
from django.utils import timezone
from opal.core.test import OpalTestCase
from opal.models import Episode, Patient
from elcid.episode_categories import InfectionService
from plugins.tb import lab, loader
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

        def create_episode(*args):
            patient, episode = self.new_patient_and_episode_please()
            episode.category_name = InfectionService.display_name
            episode.save()
            patient.demographics_set.update(
                hospital_number="111"
            )
            return patient

        create_rfh_patient_from_hospital_number.side_effect = create_episode
        loader.create_tb_episodes()
        create_rfh_patient_from_hospital_number.assert_called_once_with(
            "111", InfectionService
        )
        self.assertTrue(
            Episode.objects.filter(
                category_name=episode_categories.TbEpisode.display_name
            ).filter(
                patient__demographics__hospital_number="111"
            ).exists()
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


class RefreshFuturePatientKeyInvestigationsTestCase(OpalTestCase):
    def setUp(self):
        self.patient, _ = self.new_patient_and_episode_please()
        self.now = timezone.now()
        self.before = self.now - datetime.timedelta(10)
        self.yesterday = self.now - datetime.timedelta(1)

    def test_tb(self):
        # A Patient who tests quantifiron positive
        # then PCR negative
        lab_test = self.patient.lab_tests.create(
            test_name=lab.QuantiferonTBGold.TEST_NAME,
            test_code=lab.QuantiferonTBGold.TEST_CODE,
            datetime_ordered=self.before
        )
        lab_test.observation_set.create(
            observation_name=lab.QuantiferonTBGold.OBSERVATION_NAMES[0],
            observation_value="POSITIVE"
        )
        lab_test = self.patient.lab_tests.create(
            test_name=lab.TBPCR.TEST_NAME,
            test_code=lab.TBPCR.TEST_CODE,
            datetime_ordered=self.yesterday
        )
        lab_test.observation_set.create(
            observation_name=lab.TBPCR.OBSERVATION_NAMES[0],
            observation_value="NOT detected"
        )
        loader.refresh_patients_key_investigations(self.patient)
        tb_status = self.patient.tb_patient.get()
        self.assertEqual(
            tb_status.first_tb_positive_date,
            self.before.date(),
        )
        self.assertEqual(
            tb_status.first_tb_positive_test_type,
            lab.QuantiferonTBGold.TEST_NAME
        )
        self.assertEqual(
            tb_status.first_tb_positive_obs_value,
            "POSITIVE"
        )
        self.assertEqual(
            tb_status.recent_resulted_tb_date,
            self.yesterday.date(),
        )
        self.assertEqual(
            tb_status.recent_resulted_tb_test_type,
            lab.TBPCR.TEST_NAME
        )
        self.assertEqual(
            tb_status.recent_resulted_tb_obs_value,
            "NOT detected"
        )

    def test_ntm(self):
        # A Patient who tests quantifiron positive
        # then PCR negative
        lab_test = self.patient.lab_tests.create(
            test_name=lab.TBCulture.TEST_NAME,
            test_code=lab.TBCulture.TEST_CODE,
            datetime_ordered=self.before
        )
        lab_test.observation_set.create(
            observation_name=lab.TBCulture.OBSERVATION_NAMES[0],
            observation_value="1) Mycobacterium sp."
        )
        lab_test = self.patient.lab_tests.create(
            test_name=lab.TBCulture.TEST_NAME,
            test_code=lab.TBCulture.TEST_CODE,
            datetime_ordered=self.yesterday
        )
        lab_test.observation_set.create(
            observation_name=lab.TBCulture.OBSERVATION_NAMES[0],
            observation_value="No growth after 42 days of incubation"
        )
        loader.refresh_patients_key_investigations(self.patient)
        tb_status = self.patient.tb_patient.get()
        self.assertEqual(
            tb_status.first_ntm_positive_date,
            self.before.date(),
        )
        self.assertEqual(
            tb_status.first_ntm_positive_test_type,
            lab.TBCulture.TEST_NAME
        )
        self.assertEqual(
            tb_status.first_ntm_positive_obs_value,
            "1) Mycobacterium sp."
        )
        self.assertEqual(
            tb_status.recent_resulted_ntm_date,
            self.yesterday.date(),
        )
        self.assertEqual(
            tb_status.recent_resulted_ntm_test_type,
            lab.TBCulture.TEST_NAME
        )
        self.assertEqual(
            tb_status.recent_resulted_ntm_obs_value,
            "No growth after 42 days of incubation"
        )

import datetime
from django.utils import timezone
from opal.core.test import OpalTestCase
from opal import models as opal_models
from plugins.tb import models as tb_models
from plugins.tb import patient_lists


class TBPatientReviewTestCase(OpalTestCase):
    def test_serialize_episode(self):
        patient, episode = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name="Sally", surname="Wilson"
        )
        episode.tagging_set.create(
            value=patient_lists.TBReviewPatients.tag,
            archived=False
        )
        episode.patientconsultation_set.create(
            plan="New Regimen"
        )
        patient.bedstatus.create(
            bed="12",
            # required so that bed status serializes
            hospital_site_description=""
        )
        results = patient_lists.TBReviewPatients().to_dict(self.user)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(
            result["id"], episode.id
        )
        self.assertEqual(
            result["demographics"][0]["first_name"], "Sally"
        )
        self.assertEqual(
            result["review_patient_consultation"]["plan"], "New Regimen"
        )
        self.assertEqual(
            result["bed_statuses"][0]["bed"], "12"
        )

    def test_serializes_added_to_tb_review_list_above_other_pcs(self):
        """
        We should serialize added to TB Review List as a higher priority
        over other pcs
        """
        patient, episode = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name="Sally", surname="Wilson"
        )
        episode.tagging_set.create(
            value=patient_lists.TBReviewPatients.tag,
            archived=False
        )
        opal_models.PatientConsultationReasonForInteraction.objects.create(
            name="Added to TB review list"
        )
        pc = tb_models.PatientConsultation(episode=episode)
        pc.plan = "Contact screening"
        pc.when = timezone.now()
        pc.reason_for_interaction = "Contact screening"
        pc.save()

        pc = tb_models.PatientConsultation(episode=episode)
        pc.plan = "Added to TB review list"
        pc.when = timezone.now() - datetime.timedelta(1)
        pc.reason_for_interaction = "Added to TB review list"
        pc.save()

        patient.bedstatus.create(
            bed="12",
            # required so that bed status serializes
            hospital_site_description=""
        )
        results = patient_lists.TBReviewPatients().to_dict(self.user)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(
            result["id"], episode.id
        )
        self.assertEqual(
            result["review_patient_consultation"]["plan"], "Added to TB review list"
        )

    def test_does_not_serialize_archived_tags(self):
        _, episode = self.new_patient_and_episode_please()
        episode.tagging_set.create(
            value=patient_lists.TBReviewPatients.tag,
            archived=True
        )
        results = patient_lists.TBReviewPatients().to_dict(self.user)
        self.assertEqual(len(results), 0)

    def test_does_not_missing_tags(self):
        self.new_patient_and_episode_please()
        results = patient_lists.TBReviewPatients().to_dict(self.user)
        self.assertEqual(len(results), 0)

    def test_get(self):
        # A sanity check to make sure that we can get the template with a 200
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        response = self.client.get('/templates/tb_list_tb_review_patients.html')
        self.assertEqual(response.status_code, 200)

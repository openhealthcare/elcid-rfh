from opal.core.test import OpalTestCase
from plugins.tb import patient_lists


class TBPatientReviewTestCase(OpalTestCase):
    def test_serialize_episode(self):
        patient, episode = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            first_name="Sally", surname="Wilson"
        )
        episode.tagging_set.create(
            value=patient_lists.TBPatientReview.tag,
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
        results = patient_lists.TBPatientReview().to_dict(self.user)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(
            result["id"], episode.id
        )
        self.assertEqual(
            result["demographics"][0]["first_name"], "Sally"
        )
        self.assertEqual(
            result["recent_patient_consultation"]["plan"], "New Regimen"
        )
        self.assertEqual(
            result["bed_status"][0]["bed"], "12"
        )

    def test_does_not_serialize_archived_tags(self):
        _, episode = self.new_patient_and_episode_please()
        episode.tagging_set.create(
            value=patient_lists.TBPatientReview.tag,
            archived=True
        )
        results = patient_lists.TBPatientReview().to_dict(self.user)
        self.assertEqual(len(results), 0)

    def test_does_not_missing_tags(self):
        self.new_patient_and_episode_please()
        results = patient_lists.TBPatientReview().to_dict(self.user)
        self.assertEqual(len(results), 0)
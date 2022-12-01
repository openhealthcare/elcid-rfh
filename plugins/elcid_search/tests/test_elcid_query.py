import json
from django.urls import reverse
from opal.core.test import OpalTestCase
from plugins.elcid_search import elcid_query


class ElcidQueryTestCase(OpalTestCase):
    def test_fuzzy_query_strips_zero(self):
        """
        It should match patients that have a zero prefixed to their
        hospital number
        """
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="123"
        )
        query = elcid_query.ElcidSearchQuery(self.user, "0123")
        patients = query.fuzzy_query()
        self.assertEqual(list(patients), [patient])


class FuzzySearchIncludesMergedPatientsTestCase(OpalTestCase):
    """
    When we do a fuzzy search we should also search merged MRNs
    """
    def test_fuzzy_search_includes_merged_patients(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="123"
        )
        patient.mergedmrn_set.create(
            mrn="456"
        )
        query = elcid_query.ElcidSearchQuery(self.user, "456")
        patients = query.fuzzy_query()
        self.assertEqual(list(patients), [patient])


class PatientSummaryTestCase(OpalTestCase):
    def test_to_dict(self):
        patient, episode = self.new_patient_and_episode_please()
        patient.mergedmrn_set.create(
            mrn="234"
        )
        result = elcid_query.ElcidPatientSummary(
            patient, [episode]
        ).to_dict()
        self.assertEqual(
            result['previous_mrns'], ["234"]
        )

class IntegerationTestCase(OpalTestCase):
    def test_integration(self):
        """
        An integration test to make sure we are implementing
        the opal search api as it is expected.

        It searches for a zero prefixed merged MRN
        and returns a json structure the correct MRN
        along with the merged url
        """
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="123"
        )
        patient.mergedmrn_set.create(
            mrn="234"
        )
        url = reverse('simple_search')
        self.client.login(
            username=self.user.username, password=self.PASSWORD
        )
        resp = self.client.get(url, data={"query": "0234"})
        data = resp.json()
        self.assertEqual(len(data["object_list"]), 1)
        self.assertEqual(data["object_list"][0]["hospital_number"], "123")
        self.assertEqual(data["object_list"][0]["previous_mrns"], ["234"])

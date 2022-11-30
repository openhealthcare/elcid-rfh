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
    When we do a fuzzy search we should also search merged patients
    """
    def test_fuzzy_search_includes_merged_patients(self):
        patient, _ = self.new_patient_and_episode_please()
        patient.demographics_set.update(
            hospital_number="123"
        )
        patient.patientmerge_set.create(
            mrn="456"
        )
        query = elcid_query.ElcidSearchQuery(self.user, "456")
        patients = query.fuzzy_query()
        self.assertEqual(list(patients), [patient])

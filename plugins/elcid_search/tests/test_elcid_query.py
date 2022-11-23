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

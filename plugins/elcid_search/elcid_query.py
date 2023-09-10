from opal.core.search.queries import DatabaseQuery
from opal.models import Patient
from elcid.models import Demographics
from opal.core.search.queries import DatabaseQuery, PatientSummary
from elcid import models


class ElcidPatientSummary(PatientSummary):
    def to_dict(self):
        """
        Adds the previous mrns that have been associated with the
        patient to the patient summary.
        """
        result = super().to_dict()
        previous_merges = models.MergedMRN.objects.filter(
            patient_id=self.patient_id
        ).order_by(
            '-id'
        )
        result["previous_mrns"] = list(previous_merges.values_list('mrn', flat=True))
        return result

class ElcidSearchQuery(DatabaseQuery):
    patient_summary_class = ElcidPatientSummary

    def fuzzy_query(self):
        """
        Strips the zeros off the beginning of every item in the query.

        This is because some upstream systems prefix hospital numbers
        with zeros, so this means we will find them even if the
        user has taken the hn from another system.
        """
        query_parts = self.query.split(" ")
        self.query = " ".join(i.lstrip('0') for i in query_parts)
        self.query = self.query.strip()

        if Demographics.objects.filter(hospital_number=self.query).exists():
            return [Patient.objects.get(demographics__hospital_number=self.query)]

        return super().fuzzy_query()

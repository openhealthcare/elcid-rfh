from opal.models import Patient


class Match(object):
    matched = []
    missing = []
    partial = []


class DemographicsReconciliation(object):
    def get_queryset_to_reconcile(self):
        tenth_highest = Patient.objects.all().reverse()[10]
        return Patient.objects.filter(id__gte=tenth_highest)

    def reconcile_by_hospital_number():
        """
            look at all existing hospital numbers,
            check them and then query them against
        """

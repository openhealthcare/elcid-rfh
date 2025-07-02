"""
Reusable Utilities for EPMA
"""
from plugins.epma.models import EPMAMedOrder, EPMATherapeuticClassLookup


def get_anti_infectives_for_patient(patient):
    """
    Given a PATIENT, return med orders that are in the category 'anti-infectives'
    """
    identifiers = EPMATherapeuticClassLookup.objects.filter(
        Q(multum_hierarchy_1='anti-infectives') | Q(multum_hierarchy_2='anti-infectives')).values_list(
            'mcdx_drug_identifier', flat=True
        )
    orders = EPMAMedOrder.objects.filter(
        patient=patient,
        drug_identifier__in=identifiers
    ).order_by('-o_start_dt_tm')
    return orders

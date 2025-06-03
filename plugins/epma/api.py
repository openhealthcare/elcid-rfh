"""
APIs for EPMA data
"""
from django.shortcuts import get_object_or_404
from opal.core.api import LoginRequiredViewset
from opal.core.views import json_response
from opal.models import Patient

from plugins.epma.models import EPMAMedOrder, EPMATherapeuticClassLookup


class EPMAViewSet(LoginRequiredViewset):
    basename = 'epma'

    def retrieve(self, request, pk):
        patient = get_object_or_404(Patient.objects.all(), pk=pk)
        orders  = EPMAMedOrder.objects.filter(patient=patient).order_by('-o_start_dt_tm')

        identifiers = EPMATherapeuticClassLookup.objects.filter(
            multum_hierarchy_1='anti-infectives').values_list(
                'mcdx_drug_identifier', flat=True
            )

        anti_infectives = [o for o in orders if o.drug_identifier in identifiers]

        return json_response({
            'all': [o.to_dict() for o in orders],
            'anti_infectives': anti_infectives
        })

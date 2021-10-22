"""
API endpoint for upstream lists
"""
from opal.core.api import LoginRequiredViewset
from opal.core.views import json_response
from opal.models import Episode
from elcid.episode_categories import InfectionService
from elcid.episode_serialization import serialize
from elcid.patient_lists import PATIENT_LIST_SUBRECORDS
from plugins.icu.models import current_icu_patients


class UpstreamPatientListViewSet(LoginRequiredViewset):
    """
    We add a dynamic PatientList endpoint in this plugin to
    mirror upstream handover lists that we do not know the
    name of in advance and thus cannot declare in code.
    """
    base_name = 'patientlist/upstream'

    def retrieve(self, request, pk=None):
        patients = current_icu_patients()
        patients = patients.filter(icuhandoverlocation__ward__iexact=pk)
        episodes = Episode.objects.filter(
            patient__in=patients,
            category_name=InfectionService.display_name
        ).distinct()

        return json_response(
            serialize(episodes, request.user, subrecords=PATIENT_LIST_SUBRECORDS)
        )

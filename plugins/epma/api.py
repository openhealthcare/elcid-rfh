from opal.core.api import (
    LoginRequiredViewset, patient_from_pk
)
from opal.core.views import json_response


class EPMAMedOrder(LoginRequiredViewset):
    basename = 'epma_med_order'
    lookup_field = 'slug'

    @patient_from_pk
    def retrieve(self, request, patient):
        return json_response([
            i.to_dict() for i in patient.epmamedorder_set.all()
        ])

from rest_framework import status
from opal.core.api import SubrecordViewSet
from opal.core.views import json_response
from plugins.labtests.models import StarredObservation


class StarObservation(SubrecordViewSet):
    model = StarredObservation
    base_name = "star_observation"

    def create(self, request):
        model = self.model()
        model.update_from_dict(request.data, request.user)
        return json_response(
            {"id": model.id},
            status_code=status.HTTP_201_CREATED
        )

    def delete(self, _, pk):
        self.model.filter(id=pk).delete()
        return json_response(
            'deleted', status_code=status.HTTP_202_ACCEPTED
        )

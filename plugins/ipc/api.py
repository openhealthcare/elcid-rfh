from rest_framework import status as http_status
from opal.core.views import json_response
from opal.core.api import LoginRequiredViewset
from plugins.admissions.models import IsolatedBed


class IsolatedBedApi(LoginRequiredViewset):
    basename = "isolated_bed"

    def create(self, request):
        isolated_bed = IsolatedBed.objects.create(
            **self.request.data
        )
        return json_response(
            {'id': isolated_bed.id},
            status_code=http_status.HTTP_201_CREATED
        )

    def destroy(self, request, pk):
        IsolatedBed.objects.filter(id=pk).delete()
        return json_response(
            {}, status_code=http_status.HTTP_204_NO_CONTENT
        )

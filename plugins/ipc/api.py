from rest_framework.decorators import action
from rest_framework import status
from opal.core.views import json_response
from plugins.admissions.models import BedStatus, IsolatedBed
from opal.core.api import LoginRequiredViewset


class BedStatusApi(LoginRequiredViewset):
    basename = "bed_status"

    def serialize_instance(self, instance):
        fields = instance._meta.get_fields()
        result = {}
        for field in fields:
            result[field.name] = getattr(instance, field.name)
        result["in_isolation"] = instance.in_isolation

    @action(
        detail=False, methods=["get"], url_path="ward/(?P<ward_name>[^/.]+)"
    )
    def ward_list(self, request, ward_name):
        return json_response([
            {k: v for k, v in vars(i).items() if not k.startswith('_')} for i in BedStatus.objects.filter(ward_name=ward_name)
        ])

    @action(
        detail=True,
        methods=["put"],
        url_path="(?P<bed_status_pk>[^/.]+)/isolate/",
    )
    def isolate_bed(self, request, bed_status_pk):
        bed_status = BedStatus.objects.get(id=bed_status_pk)
        IsolatedBed.objects.create(
            hospital_site_code=bed_status.hospital_site_code,
            ward_name=bed_status.ward_name,
            room=bed_status.room,
            bed=bed_status.bed
        )
        return json_response({}, status_code=status.HTTP_204_NO_CONTENT)

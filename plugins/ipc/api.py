from rest_framework.decorators import action
from rest_framework import status
from django.utils.functional import cached_property
from opal.core.views import json_response
from plugins.admissions.models import BedStatus, IsolatedBed
from opal.core.api import LoginRequiredViewset


class BedStatusApi(LoginRequiredViewset):
    basename = "bed_status"

    @cached_property
    def isolated_beds(self):
        bed_statuses = IsolatedBed.objects.values_list(
            "hospital_site_code", "ward_name", "room", "bed"
        )
        return set([tuple(i) for i in bed_statuses])

    def serialize_instance(self, instance):
        fields = instance._meta.get_fields()
        result = {}
        for field in fields:
            if field.name == "patient":
                continue
            result[field.name] = getattr(instance, field.name)
        key = (
            instance.hospital_site_code,
            instance.ward_name,
            instance.room,
            instance.bed,
        )
        result["in_isolation"] = key in self.isolated_beds
        if instance.patient_id:
            result["comments"] = instance.patient.ipcstatus_set.all()[0].comments
        return result

    @action(detail=False, methods=["get"], url_path="ward/(?P<ward_name>[^/.]+)")
    def ward_list(self, request, ward_name):
        return json_response(
            [
                self.serialize_instance(i)
                for i in BedStatus.objects.filter(ward_name=ward_name).prefetch_related(
                    "patient__ipcstatus_set"
                )
            ]
        )

    @action(
        detail=True,
        methods=["put"],
        url_path="isolate",
    )
    def isolate_bed(self, request, pk):
        bed_status = BedStatus.objects.get(id=pk)
        IsolatedBed.objects.create(
            hospital_site_code=bed_status.hospital_site_code,
            ward_name=bed_status.ward_name,
            room=bed_status.room,
            bed=bed_status.bed,
        )
        return json_response({}, status_code=status.HTTP_204_NO_CONTENT)

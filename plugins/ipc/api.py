from rest_framework.decorators import action
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
            result[field.name] = getattr(instance, field.name)
        result["in_isolation"] = self.bed_statuses[
            (
                instance.hospital_site_code,
                instance.ward_name,
                instance.room,
                instance.bed,
            )
        ]

    @action(detail=False, methods=["get"], url_path="ward/(?P<ward_name>[^/.]+)")
    def ward_list(self, request, ward_name):
        return json_response(
            [
                {k: v for k, v in vars(i).items() if not k.startswith("_")}
                for i in BedStatus.objects.filter(ward_name=ward_name)
            ]
        )

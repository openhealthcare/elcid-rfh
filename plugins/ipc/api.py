import collections
from rest_framework.decorators import action
from rest_framework import status as http_status
from django.utils.functional import cached_property
from opal.core.views import json_response
from opal.core.api import LoginRequiredViewset
from plugins.admissions.models import BedStatus, IsolatedBed
from plugins.admissions.constants import RFH_HOSPITAL_SITE_CDOE
from plugins.ipc.episode_categories import IPCEpisode


class BedStatusApi(LoginRequiredViewset):
    basename = "bed_status"

    @cached_property
    def isolated_beds(self):
        bed_statuses = IsolatedBed.objects.values_list(
            "hospital_site_code", "ward_name", "room", "bed"
        )
        return set([tuple(i) for i in bed_statuses])

    def in_isolation(self, bed_status):
        if bed_status.room and bed_status.room.startswith('SR'):
            return True
        key = (
            bed_status.hospital_site_code,
            bed_status.ward_name,
            bed_status.room,
            bed_status.bed,
        )
        return key in self.isolated_beds

    def serialize_instance(self, instance):
        fields = instance._meta.get_fields()
        result = {}
        for field in fields:
            if field.name == "patient":
                continue
            result[field.name] = getattr(instance, field.name)
        result["in_isolation"] = self.in_isolation(instance)
        if instance.patient_id:
            result["demographics"] = instance.patient.demographics_set.all()[0].to_dict(
                self.request
            )
            result["comments"] = instance.patient.ipcstatus_set.all()[0].comments
            episodes = instance.patient.episode_set.all()
            ipc_episodes = [i for i in episodes if i.category_name == IPCEpisode.display_name]
            if ipc_episodes:
                result['episode_id'] = ipc_episodes[0].episode_id
        return result

    @action(detail=False, methods=["get"], url_path="isolation")
    def isolation(self, request):
        side_room_statuses = list(BedStatus.objects.filter(
            room__startswith='SR'
        ))
        other_statuses = BedStatus.objects.filter(
            hospital_site_code=RFH_HOSPITAL_SITE_CDOE,
        ).exclude(
            room__startswith='SR'
        )
        isolated_statuses = [i for i in other_statuses if self.in_isolation(i)]
        statuses = BedStatus.objects.filter(
            id__in=[i.id for i in side_room_statuses + isolated_statuses]
        ).order_by(
            'ward_name', 'bed'
        ).prefetch_related(
            'patient__episode_set',
            'patient__ipcstatus_set',
            'patient__demographics_set',
        )
        wards = collections.defaultdict(list)
        for status in statuses:
            wards[status.ward_name].append(self.serialize_instance(status))
        return json_response({
            "location_count": len(statuses),
            "wards": wards
        })

    @action(detail=False, methods=["get"], url_path="ward/(?P<ward_name>[^/.]+)")
    def ward_list(self, request, ward_name):
        statuses = BedStatus.objects.filter(ward_name=ward_name).order_by(
            'ward_name', 'bed'
        ).prefetch_related(
            'patient__episode_set',
            "patient__ipcstatus_set",
            'patient__demographics_set',
        )
        return json_response({
            "patients": [self.serialize_instance(i) for i in statuses]
        })

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
        return json_response({}, status_code=http_status.HTTP_204_NO_CONTENT)

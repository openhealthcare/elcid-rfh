"""
APIs for the IPC Module
"""
from rest_framework import status as http_status
from opal.core.views import json_response
from opal.core.api import LoginRequiredViewset

from plugins.admissions.models import IsolatedBed

from plugins.ipc import constants, models


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


class SideroomAPI(LoginRequiredViewset):
    basename = 'sideroomlist'

    def retrieve(self, request, pk):
        user = request.user

        # Temporary while we run two in parallel
        from plugins.ipc.views import SideRoomView
        context = SideRoomView().get_context_data(hospital_code=pk)


        hospital_name = constants.HOSPITAL_NAMES[pk]

        ward_names = list(context['wards'].keys())

        def for_angular(bedstatus):

            ipc_episode_id = None

            if getattr(bedstatus, 'ipc_episode', False):
                ipc_episode_id = bedstatus.ipc_episode.id

            data = {
                'room'          : bedstatus.room,
                'ward_name'     : bedstatus.ward_name,
                'bed'           : bedstatus.bed,
                'bed_status'    : bedstatus.bed_status,
                'admitted'      : bedstatus.get_admitted_as_dt(),
                'is_open_bay'   : getattr(bedstatus, 'is_open_bay', False),
                'is_rogue'      : getattr(bedstatus, 'is_rogue', False),
                'ipc_episode_id': ipc_episode_id
            }

            if bedstatus.patient:
                demographics = bedstatus.patient.demographics()
                demographic_data = {
                    'mrn'           : demographics.hospital_number,
                    'name'          : demographics.name,
                    'patient_id'    : demographics.patient_id,
                    'dob'           : demographics.date_of_birth,
                    'sex'           : demographics.sex
                }

                data.update(demographic_data)

                sideroom_status = bedstatus.patient.sideroomstatus_set.get()
                data['sideroom_status'] = sideroom_status.to_dict(user)

                ipc_status = bedstatus.patient.ipcstatus_set.get()
                data['flags'] = ipc_status.get_flags()

            return data

        ward_data = []
        for ward_name, beds in context['wards'].items():
            ward_data.append({'name': ward_name, 'beds': [for_angular(b) for b in beds]})


        return json_response(
            {
                'metadata': {
                    'hospital_name': hospital_name,
                    'hospital_code': pk,
                    'male'         : context['male'],
                    'female'       : context['female'],
                    'flags'        : list(models.IPCStatus.FLAGS.keys()),
                    'ward_names'   : ward_names
                },
                'wards': ward_data
            }
        )

"""
API for admission data
"""
from collections import defaultdict
from django.shortcuts import get_object_or_404
from django.utils import timezone, timesince
from opal.core.api import LoginRequiredViewset, patient_from_pk
from opal.models import Patient
from opal.core.views import json_response

from plugins.admissions.models import TransferHistory
from plugins.admissions import constants

EXCLUDE_ADMISSIONS = [
    # We previously excluded these based on eyeballing data for admissions before
    # we had learned to update them in place adequately.
    # These message types are under active review, and the existing list definitely
    # excluded current active admissions e.g. patients in the building where
    # we had valid location data for them.

    # 'A14', # Pending admit
    # 'A35', # Merge account num
    # 'S12', # New Appt
    # 'S13', # Reschedule Appt
    # 'S14', # Modify Appt
    # 'S15'  # Cancel Appt
]

class AdmissionViewSet(LoginRequiredViewset):
    basename = 'admissions'

    def retrieve(self, request, pk):
        patient    = get_object_or_404(Patient.objects.all(), pk=pk)
        admissions = patient.encounters.exclude(
            msh_9_msg_type__in=EXCLUDE_ADMISSIONS
        ).order_by('last_updated')
        return json_response([a.to_dict() for a in admissions])


class LocationHistoryViewSet(LoginRequiredViewset):
    basename = 'location_history'

    def get_duration(self, first_datetime, second_datetime):
        if first_datetime and second_datetime and second_datetime <= timezone.now():
            return timesince.timesince(first_datetime, second_datetime)

    def get_title(self, location_histories):
        by_start_datetime = sorted(
            location_histories, key=lambda x: x.transfer_start_datetime
        )
        transfer_start_datetime = by_start_datetime[0].transfer_start_datetime
        transfer_end_datetime = by_start_datetime[-1].transfer_end_datetime
        if transfer_end_datetime > timezone.now():
            transfer_end_datetime = None
        return {
            'spell_number': location_histories[0].spell_number,
            'encounter_id': location_histories[0].encounter_id,
            'transfer_start_datetime': transfer_start_datetime,
            'transfer_end_datetime': transfer_end_datetime,
            'duration': self.get_duration(transfer_start_datetime, transfer_end_datetime)
        }

    def get_table_data(self, location_histories):
        location_histories = sorted(
            location_histories, key=lambda x: x.transfer_start_datetime
        )
        result = []
        for location_history in location_histories:
            fields = [
                "transfer_sequence_number",
                "transfer_start_datetime",
                "transfer_end_datetime",
                "transfer_location_code",
                "unit",
                "room",
                "bed",
                "transfer_reason",
            ]
            row = {field: getattr(location_history, field) for field in fields}
            row['duration'] = self.get_duration(
                location_history.transfer_start_datetime,
                location_history.transfer_end_datetime
            )
            row['hospital'] = constants.HOSPITAL_CODES_TO_DISPLAY.get(
                location_history.site_code
            )
            result.append(row)
        return result

    @patient_from_pk
    def retrieve(self, request, patient):
        """
        Returns the data for the location history detail page
        e.g.

        [{
            title: {
                transfer_start_datetime: 12/12/2000 12:14,
                transfer_end_datetime: 12/12/2000 18:14,
                spell_number: xx,
                encounter_id: xx
            },
            table_data: [
                {
                    transfer_sequence_number: 123,
                    transfer_start_datetime: 12/12/2000 12:14,
                    transfer_end_datetime: 12/12/2000 13:14,
                    unit: 'B1',
                    room: '12',
                    bed: '1',
                    transfer_reason: 'some reason'
                },
                {
                    ...
                },
            ]
        }]
        """
        transfer_histories = patient.transferhistory_set.all()
        by_spell_encounter_id = defaultdict(list)
        for transfer_history in transfer_histories:
            key = (transfer_history.spell_number, transfer_history.encounter_id,)
            by_spell_encounter_id[key].append(transfer_history)

        result = []
        for location_histories in by_spell_encounter_id.values():
            result.append({
                'title': self.get_title(location_histories),
                'table_data': self.get_table_data(location_histories),
            })

        result = sorted(
            result,
            key=lambda x: x['title']['transfer_start_datetime'],
            reverse=True
        )
        return json_response(result)

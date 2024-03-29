"""
Views for the Admissions module
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import DetailView, TemplateView
from opal.models import Patient

from plugins.admissions.models import Encounter, TransferHistory, BedStatus


class UpstreamLocationSnippet(LoginRequiredMixin, DetailView):
    template_name = 'admissions/partials/upstream_location.html'
    model         = Patient

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        if self.object.upstreamlocation.exists():
            location = self.object.upstreamlocation.get()
            context['location'] = location

        return context


class BedboardHospitalListView(LoginRequiredMixin, TemplateView):

    template_name = 'bedboard/hospital_list.html'


    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        context['hospitals'] = BedStatus.objects.values_list(
            'hospital_site_description', 'hospital_site_code').distinct().order_by('hospital_site_code')

        return context


class BedboardHospitalDetailView(LoginRequiredMixin, TemplateView):

    template_name = 'bedboard/hospital_detail.html'


    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        context['hospital'] = BedStatus.objects.filter(
            hospital_site_code=k['hospital_code']).first().hospital_site_description
        context['wards'] = BedStatus.objects.filter(hospital_site_code=k['hospital_code']).values_list(
            'ward_name', flat=True).distinct().order_by('ward_name')

        return context


class BedboardWardDetailView(LoginRequiredMixin, TemplateView):

    template_name = 'bedboard/ward_detail.html'


    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        context['patients'] = BedStatus.objects.filter(ward_name=k['ward_name']).order_by('bed')

        return context




class SpellLocationHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'admissions/transfer_history.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        encounter = Encounter.objects.filter(
            pid_18_account_number=k['spell_number']
        ).first()
        history = TransferHistory.objects.filter(spell_number=k['spell_number'])
        patient = None
        demographics = None

        if encounter:
            patient = encounter.patient
            demographics = patient.demographics()

        context['patient']      = patient
        context['demographics'] = demographics
        context['encounter']    = encounter
        context['history']      = history

        return context


class SliceContactsView(LoginRequiredMixin, TemplateView):

    template_name = 'admissions/slice_contacts.html'



    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        transfer  = TransferHistory.objects.get(encounter_slice_id=k['slice_id'])
        encounter = Encounter.objects.filter(
            pid_18_account_number=transfer.spell_number
        ).first()

        context['source']  = transfer
        context['encounter'] = encounter
        context['index_patient'] = transfer.patient
        context['index_demographics'] = transfer.patient.demographics()

        contact_transfers = TransferHistory.objects.filter(
            transfer_start_datetime__lte=transfer.transfer_end_datetime,
            transfer_end_datetime__gte=transfer.transfer_start_datetime,
            unit=transfer.unit,
            room=transfer.room
        ).exclude(
            mrn=transfer.mrn
        ).order_by('bed', 'transfer_start_datetime').prefetch_related(
            'patient__demographics_set'
        )

        context['now'] = timezone.now()
        context['transfers'] = contact_transfers
        context['num_contacts'] = len(set(t.mrn for t in contact_transfers))

        return context


class LocationHistoryEncounterContactsView(LoginRequiredMixin, TemplateView):
    template_name = 'admissions/encounter_contacts.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        context['now'] = timezone.now()

        encounter_id = k['encounter_id']
        context['encounter_id'] = encounter_id

        slices = TransferHistory.objects.filter(
            encounter_id=encounter_id
        ).order_by('transfer_start_datetime').prefetch_related(
            'patient__demographics_set'
        )

        for transfer in slices:
            contact_transfers = TransferHistory.objects.filter(
                transfer_start_datetime__lte=transfer.transfer_end_datetime,
                transfer_end_datetime__gte=transfer.transfer_start_datetime,
                unit=transfer.unit,
                room=transfer.room
            ).exclude(
                mrn=transfer.mrn
            ).order_by('bed', 'transfer_start_datetime').prefetch_related(
                'patient__demographics_set'
            )
            transfer.contact_transfers = contact_transfers

            # We use these for toggling show hide, when they're -ve numbers
            # it breaks the angular variable naming
            transfer.abs_encounter_slice_id = abs(transfer.encounter_slice_id)

        context['slices'] = slices

        context['index_patient'] = slices[0].patient
        context['index_demographics'] = slices[0].patient.demographics()

        return context


class LocationHistoryEncounterRemainingInpatientContactsView(LoginRequiredMixin, TemplateView):
    template_name = 'admissions/remaining_encounter_contacts.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        now = timezone.now()
        context['now'] = now

        encounter_id = k['encounter_id']
        context['encounter_id'] = encounter_id

        slices = TransferHistory.objects.filter(
            encounter_id=encounter_id
        ).order_by('transfer_start_datetime').prefetch_related(
            'patient__demographics_set'
        )

        patients = set()

        for transfer in slices:
            contact_transfers = TransferHistory.objects.filter(
                transfer_start_datetime__lte=transfer.transfer_end_datetime,
                transfer_end_datetime__gte=now,
                unit=transfer.unit,
                room=transfer.room
            ).exclude(
                mrn=transfer.mrn
            ).prefetch_related(
                'patient__demographics_set'
            )
            for contact in contact_transfers:
                patient = contact.patient
                if patient.bedstatus.count() > 0:
                    patient.index_location = transfer.location()
                    patient.contact_location = contact.location()
                    patients.add(patient)

        context['patients'] = patients

        context['index_patient'] = slices[0].patient
        context['index_demographics'] = slices[0].patient.demographics()

        return context




class LocationHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'admissions/location_history.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        location_code = k['location_code']

        history = TransferHistory.objects.filter(
            transfer_location_code=location_code,
        ).order_by('-transfer_start_datetime').prefetch_related(
            'patient__demographics_set'
        )
        first = history[0]
        context['location'] = f"{first.site_code} {first.unit} {first.room} {first.bed}"

        context['history'] = history
        context['location_code'] = location_code
        context['now'] = timezone.now()

        return context

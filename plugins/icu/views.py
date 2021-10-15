"""
Views for the ICU plugin
"""
import collections
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone
from opal.models import (
    Episode, Clinical_advice_reason_for_interaction, Patient
)

from elcid.episode_categories import InfectionService
from elcid.models import MicrobiologyInput
from plugins.admissions.models import UpstreamLocation
from plugins.covid.models import CovidPatient
from plugins.icu import constants


class ICUDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'icu/dashboard.html'

    def get_current_icu_patients(self):
        """
        The upstream Freenet ICU Handover view sometimes leaves patients permanently in
        an undischarged state when they are on 'ghost' wards - temporary wards that
        existed during an ICU surge, and were then removed from the Freenet application
        before all patients had been removed on their database.

        We believe a patient is _actually_ on ICU if they either:
        - Have an ICU admission date within the last 4 days
        - Received ICU clinical advice within the last 4 days
        """
        four_days_ago = timezone.now() - datetime.timedelta(4)
        icu_locations = UpstreamLocation.objects.filter(ward__in=constants.WARD_NAMES)
        patient_ids_within_four_days = set(icu_locations.filter(
            admitted__gte=four_days_ago
        ).values_list('patient_id', flat=True).distinct())

        icu_round_reason = Clinical_advice_reason_for_interaction.objects.get(
            name=MicrobiologyInput.ICU_REASON_FOR_INTERACTION
        )

        review_within_four_days = set(MicrobiologyInput.objects.filter(
            when__gte=four_days_ago,
            reason_for_interaction_fk_id=icu_round_reason.id
        ).values_list('episode__patient_id', flat=True))

        patient_ids_within_four_days.update(review_within_four_days)
        return Patient.objects.filter(
            id__in=patient_ids_within_four_days
        )

    def get_ward_to_patients(self):
        icu_patients = self.get_current_icu_patients().prefetch_related("upstreamlocation")
        ward_to_patients = collections.defaultdict(list)
        for icu_patient in icu_patients:
            for upstream_location in icu_patient.upstreamlocation.all():
                if upstream_location.ward in constants.WARD_NAMES:
                    ward_to_patients[upstream_location.ward].append(icu_patient)
        return ward_to_patients

    def get_ward_info(self, ward_name, patients):
        """
        Given a WARD_NAME string, return summary info about that ICU ward
        """
        covid_patients = CovidPatient.objects.filter(
            patient__in=patients
        ).count()

        info = {
            'name'          : ward_name,
            'patient_count' : len(patients),
            'covid_patients': covid_patients,
            'patients'      : self.get_patient_info(ward_name, patients)
        }
        return info

    def get_patient_info(self, ward, patients):
        info = []
        icu_round_reason = Clinical_advice_reason_for_interaction.objects.get(
            name=MicrobiologyInput.ICU_REASON_FOR_INTERACTION
        )
        episodes = Episode.objects.filter(
            patient__in=patients,
            category_name=InfectionService.display_name
        )

        for episode in episodes:
            patient = episode.patient
            bed = UpstreamLocation.objects.filter(
                    patient=patient, ward=ward
            ).order_by(
                '-admitted'
            ).first().bed
            record = {
                'episode'     : episode,
                'demographics': patient.demographics(),
                'last_review' : episode.microbiologyinput_set.filter(
                    reason_for_interaction_fk=icu_round_reason
                ).order_by('when').last(),
                'bed' : bed,
                'infection_note' : episode.infectionservicenote_set.get().text
            }
            info.append(record)

        info = sorted(info, key=lambda x: x['bed'])
        return info

    def get_context_data(self, *a, **k):
        context = super(ICUDashboardView, self).get_context_data(*a, **k)
        ward_to_patients = self.get_ward_to_patients()
        wards = []
        for ward_name, patients in ward_to_patients.items():
            wards.append(self.get_ward_info(ward_name, patients))

        context['wards'] = wards
        context['icu_patients'] = 0
        if ward_to_patients:
            context['icu_patients'] = sum(
                [len(patients) for patients in ward_to_patients.values()]
            )
        context['today'] = datetime.date.today()
        return context

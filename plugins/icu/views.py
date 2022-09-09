"""
Views for the ICU plugin
"""
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from opal.models import (
    Episode, Clinical_advice_reason_for_interaction, Patient
)

from elcid.episode_categories import InfectionService
from elcid.models import MicrobiologyInput
from plugins.admissions.models import BedStatus
from plugins.covid.models import CovidPatient
from plugins.icu import constants


class ICUDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'icu/dashboard.html'

    def get_ward_info(self, ward_name):
        """
        Given a WARD_NAME string, return summary info about that ICU ward
        """
        patients = Patient.objects.filter(bedstatus__ward_name=ward_name)

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

            bed = BedStatus.objects.filter(
                    patient=patient, ward_name=ward
            ).order_by(
                '-updated_date'
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
        wards = []
        for ward_name in constants.WARD_NAMES:
            ward_info = self.get_ward_info(ward_name)
            if ward_info["patient_count"]:
                wards.append(ward_info)

        context['wards'] = wards
        context['icu_patients'] = 0
        if wards:
            context['icu_patients'] = sum(
                [ward_info["patient_count"] for ward_info in wards]
            )
        context['today'] = datetime.date.today()
        return context

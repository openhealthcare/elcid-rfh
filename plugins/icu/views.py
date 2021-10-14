"""
Views for the ICU plugin
"""
import collections
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from opal.models import Episode, Clinical_advice_reason_for_interaction

from elcid.episode_categories import InfectionService
from elcid.models import MicrobiologyInput
from plugins.covid.models import CovidPatient

from plugins.icu.models import ICUWard, ICUHandoverLocation, current_icu_patients


class ICUDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'icu/dashboard.html'

    def get_ward_info(self, ward_name):
        """
        Given a WARD_NAME string, return summary info about that ICU ward
        """
        today = datetime.date.today()

        try:
            beds     = ICUWard.objects.get(name=ward_name).beds
        except ICUWard.DoesNotExist:
            beds = None
        handover_patients = ICUHandoverLocation.objects.filter(
            ward=ward_name,
            patient__in=current_icu_patients()
        )

        handover_patient_count = handover_patients.count()
        covid_patients = CovidPatient.objects.filter(
            patient__in=[p.patient for p in handover_patients]
        ).count()

        stays       = [
            (today - p.admitted).days +1 for p in handover_patients if p.admitted
        ]
        staycounter = collections.defaultdict(int)

        for stay in stays:
            staycounter[stay] += 1

        timeseries = ['Patients']
        ticks      = ['x']

        if handover_patient_count > 0:
            y_axis_upper_bound = max(staycounter.values()) + 1
        else:
            y_axis_upper_bound = 1

        for stay in sorted(staycounter.keys()):
            ticks.append(stay)
            timeseries.append(staycounter[stay])


        info = {
            'name'          : ward_name,
            'beds'          : beds,
            'patient_count' : handover_patient_count,
            'covid_patients': covid_patients,
            'stay'          : [ticks, timeseries],
            'yticks'        : list(range(1, y_axis_upper_bound)),
            'link'          : f'/#/list/upstream/{ward_name}',
            'patients'      : self.get_patient_info(ward_name)
        }
        return info

    def get_patient_info(self, ward_name):
        info = []
        icu_round_reason = Clinical_advice_reason_for_interaction.objects.get(
            name=MicrobiologyInput.ICU_REASON_FOR_INTERACTION
        )
        episodes = Episode.objects.filter(
            patient__icuhandoverlocation__ward=ward_name,
            patient__in=current_icu_patients(),
            category_name=InfectionService.display_name
        ).order_by('patient__icuhandoverlocation__bed')

        for episode in episodes:
            patient = episode.patient
            record = {
                'episode'     : episode,
                'demographics': patient.demographics(),
                'last_review' : episode.microbiologyinput_set.filter(
                    reason_for_interaction_fk=icu_round_reason
                ).order_by('when').last(),
                'handoverlocation' : patient.icuhandoverlocation_set.get(),
                'infection_note' : episode.infectionservicenote_set.get().text
            }
            info.append(record)

        return info

    def get_context_data(self, *a, **k):
        context = super(ICUDashboardView, self).get_context_data(*a, **k)
        wards = []
        qs = ICUHandoverLocation.objects.filter(
            patient__in=current_icu_patients()
        )
        for ward_name in sorted(qs.values_list(
                'ward', flat=True).distinct()):
            wards.append(self.get_ward_info(ward_name))

        context['wards'] = wards
        context['icu_patients'] = qs.count()
        context['today'] = datetime.date.today()

        return context

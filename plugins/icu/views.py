"""
Views for the ICU plugin
"""
import collections
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from plugins.covid.models import CovidPatient

from plugins.icu import constants
from plugins.icu.models import ICUWard, ICUHandoverLocation

WARD_LISTS = {
    'South': 'autoic_u_south',
    'East': 'autoic_u_east',
    'West': 'autoic_u_west',
    'ICU 2': 'autoic_u_2',
    'SHDU': 'icu_shdu'
}


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
        handover_patients = ICUHandoverLocation.objects.filter(ward=ward_name)

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
            'link'          : '/#/list/{}'.format(WARD_LISTS[ward_name])
        }
        return info

    def get_context_data(self, *a, **k):
        context = super(ICUDashboardView, self).get_context_data(*a, **k)
        wards = []
        for ward_name in constants.WARD_NAMES:
            wards.append(self.get_ward_info(ward_name))

        context['wards'] = wards
        context['icu_patients'] = ICUHandoverLocation.objects.all().count()

        return context

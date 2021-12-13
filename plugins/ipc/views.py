"""
Views for the IPC module
"""
import collections
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from plugins.admissions.models import Encounter, UpstreamLocation, BedStatus

from plugins.ipc import lab, models, utils


class IPCHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'ipc/home.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        alerts  = models.InfectionAlert.objects.filter(seen=False).order_by('-trigger_datetime')
        context['alerts'] = alerts

        monthly = collections.defaultdict(lambda: collections.defaultdict(int))

        today = datetime.date.today()
        start = datetime.date(today.year-2, today.month, 1)

        for alert in models.InfectionAlert.objects.filter(trigger_datetime__gte=start):
            key = datetime.date(alert.trigger_datetime.year, alert.trigger_datetime.month, 1)
            monthly[key][alert.category] += 1

        ticks  = ['x'] + ['{0}-{1:02d}-01'.format(d.year, d.month) for d in sorted(monthly.keys())[-12:]]
        cdiffs = ['C. Diff'] + [monthly[k][models.InfectionAlert.CDIFF] for k in sorted(monthly.keys())[-12:]]
        cpes   = ['CPE'] + [monthly[k][models.InfectionAlert.CPE] for k in sorted(monthly.keys())[-12:]]
        mrsas  = ['MRSA'] + [monthly[k][models.InfectionAlert.MRSA] for k in sorted(monthly.keys())[-12:]]
        tbs    = ['TB'] + [monthly[k][models.InfectionAlert.TB] for k in sorted(monthly.keys())[-12:]]
        vres   = ['VRE'] + [monthly[k][models.InfectionAlert.VRE] for k in sorted(monthly.keys())[-12:]]

        context['overview_data'] = [ticks, cdiffs, cpes, mrsas, tbs, vres]

        RFH = 'RAL01'

        context['rfh_patients'] = BedStatus.objects.filter(hospital_site_code=RFH, bed_status='Occupied').count()
        context['rfh_beds_available'] = BedStatus.objects.filter(hospital_site_code=RFH, bed_status='Available').count()
        context['rfh_siderooms'] = BedStatus.objects.filter(hospital_site_code=RFH, room__startswith='SR',
                                                            bed_status='Occupied').count()

        context['weekly_alerts'] = models.InfectionAlert.objects.filter(
            trigger_datetime__gte=today-datetime.timedelta(days=7)).count()

        return context


class RecentTestsView(LoginRequiredMixin, TemplateView):
    template_name = 'ipc/recent_tests.html'
    num_tests    = 50

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        test = lab.get_test_class_by_code(k['test_code'])
        context['test_name'] = test.TEST_NAME
        context['tests'] = lab.get_test_instances(test, num=self.num_tests)
        return context


class HospitalWardListView(LoginRequiredMixin, TemplateView):
    template_name = 'ipc/ward_list.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        context['hospital'] = BedStatus.objects.filter(
            hospital_site_code=k['hospital_code']).first().hospital_site_description

        context['wards'] = BedStatus.objects.filter(hospital_site_code=k['hospital_code']).values_list(
            'ward_name', flat=True).distinct().order_by('ward_name')

        return context


class WardDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'ipc/ward_detail.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        context['patients'] = BedStatus.objects.filter(ward_name=k['ward_name']).order_by('bed')

        return context


class SideRoomView(LoginRequiredMixin, TemplateView):
    template_name = 'ipc/siderooms.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        patients = UpstreamLocation.objects.filter(
            ward__startswith='RAL',
            room__startswith='SR'
        ).exclude(
            ward__startswith='RAL BH'
        ).order_by('ward', 'bed')

        context['patients'] = patients

        return context



class AlertListView(LoginRequiredMixin, TemplateView):
    template_name = 'ipc/alert_list.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        alerts = models.InfectionAlert.objects.filter(
            category=k['alert_code']).order_by('-trigger_datetime')

        monthly = collections.defaultdict(int)
        for alert in alerts:
            key = datetime.date(alert.trigger_datetime.year, alert.trigger_datetime.month, 1)
            monthly[key] += 1

        ticks = ['x'] + ['{0}-{1:02d}-01'.format(d.year, d.month) for d in sorted(monthly.keys())]
        counts = [k['alert_code']] + [monthly[k] for k in sorted(monthly.keys())]

        context['alert_data'] = [ticks, counts]
        context['alerts'] = alerts[:40]
        context['alert_code'] = k['alert_code']

        return context

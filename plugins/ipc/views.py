"""
Views for the IPC module
"""
import collections
import datetime
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import TemplateView, View
from django.utils import timezone
from opal.core.views import json_response

from elcid.utils import natural_keys, find_patients_from_mrns
from plugins.admissions.constants import RFH_HOSPITAL_SITE_CODE, BARNET_HOSPITAL_SITE_CODE
from plugins.admissions.models import BedStatus, IsolatedBed, TransferHistory

from plugins.ipc import lab, models, constants


def sort_rfh_wards(text):
    """
    RFH ward names brak natural keys
    """
    tower = False
    if re.match('RF-[0-9]', text):
        tower = True

    text = text.replace('RF-', '')
    keys = natural_keys(text)

    if tower:
        keys.insert(0, 'z')

    return keys

def sort_sideroom_beds(bed):
    """
    Ordering of beds in sideroom list is not by location.
    It's a proxy for priority:
    Siderooms > Open Bays > Rogue patients
    """
    if getattr(bed, 'is_rogue', False):
        return (3, bed.bed)
    if getattr(bed, 'is_open_bay', False):
        return (2, bed.bed)
    return (1, bed.bed)


class IPCHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'ipc/home.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        # alerts  = models.InfectionAlert.objects.filter(seen=False).order_by('-trigger_datetime')
        # context['alerts'] = alerts
        # monthly = collections.defaultdict(lambda: collections.defaultdict(int))
        # today = datetime.date.today()
        # start = datetime.date(today.year-2, today.month, 1)
        # for alert in models.InfectionAlert.objects.filter(trigger_datetime__gte=start):
        #     key = datetime.date(alert.trigger_datetime.year, alert.trigger_datetime.month, 1)
        #     monthly[key][alert.category] += 1

        # ticks  = ['x'] + ['{0}-{1:02d}-01'.format(d.year, d.month) for d in sorted(monthly.keys())[-12:]]
        # cdiffs = ['C. Diff'] + [monthly[k][models.InfectionAlert.CDIFF] for k in sorted(monthly.keys())[-12:]]
        # cpes   = ['CPE'] + [monthly[k][models.InfectionAlert.CPE] for k in sorted(monthly.keys())[-12:]]
        # mrsas  = ['MRSA'] + [monthly[k][models.InfectionAlert.MRSA] for k in sorted(monthly.keys())[-12:]]
        # tbs    = ['TB'] + [monthly[k][models.InfectionAlert.TB] for k in sorted(monthly.keys())[-12:]]
        # vres   = ['VRE'] + [monthly[k][models.InfectionAlert.VRE] for k in sorted(monthly.keys())[-12:]]

        # context['overview_data'] = [ticks, cdiffs, cpes, mrsas, tbs, vres]


        # context['rfh_patients'] = BedStatus.objects.filter(
        #     hospital_site_code=RFH_HOSPITAL_SITE_CODE, bed_status='Occupied').count()


        # context['barnet_patients'] = BedStatus.objects.filter(
        #     hospital_site_code=BARNET_HOSPITAL_SITE_CODE, bed_status='Occupied').count()

        # context['weekly_alerts'] = models.InfectionAlert.objects.filter(
        #     trigger_datetime__gte=today-datetime.timedelta(days=7)).count()

        flag_labels = {v: k for k, v in models.IPCStatus.FLAGS.items()}

        flagged = []
        flags = [
            'mrsa', 'c_difficile', 'vre', 'candida_auris',
            'carb_resistance',
            'multi_drug_resistant_organism', 'covid_19'
        ]
        sites = [('RFH', 'RAL01'), ('Barnet', 'RAL26')]

        for name, site in sites:
            counts = {}

            for flag in flags:
                kwargs = {
                    f"patient__ipcstatus__{flag}": True,
                    "hospital_site_code": site
                }
                counts[flag_labels[flag]] = BedStatus.objects.filter(
                    **kwargs
                ).count()

            flagged.append((name, site, counts))

        context['flagged'] = flagged
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

        wards = BedStatus.objects.filter(
            hospital_site_code=k['hospital_code']
        ).exclude(ward_name__in=constants.WARDS_TO_EXCLUDE_FROM_LIST).values_list(
            'ward_name', flat=True).distinct()


        wards = sorted(wards, key=natural_keys)

        context['hospital'] = BedStatus.objects.filter(
            hospital_site_code=k['hospital_code']).first().hospital_site_description

        context['wards'] = wards
        context['hospital_ward_template'] = f"ipc/{k['hospital_code']}_ward_list.html"

        return context


class WardDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'ipc/ward_detail.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        locations = BedStatus.objects.filter(
            ward_name=k['ward_name']).exclude(bed__startswith="Cap").order_by('bed')

        for location in locations:
            if location.room.startswith('SR'):
                location.is_sideroom = True
            if location.isolated_bed:
                location.is_sideroom = True

            if location.patient:
                ipc = location.patient.episode_set.filter(category_name='IPC').first()
                if ipc:
                    location.ipc_episode = ipc

        context['patients'] = locations
        context['patient_count'] = sum([1 for l in locations if l.patient])

        return context


class WardDetailHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'ipc/ward_history_detail.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        days_ago = datetime.date.today() - datetime.timedelta(31)
        slices = TransferHistory.objects.filter(
            unit=k['ward_name']
        ).exclude(
            transfer_end_datetime__lte=days_ago,
        ).order_by('bed', 'transfer_end_datetime')

        for transfer in slices:
            ipc = transfer.patient.episode_set.filter(category_name='IPC').first()
            if ipc:
                transfer.ipc_episode = ipc

        context['slices'] = slices
        context['now'] = timezone.now()

        return context



class SideRoomView(LoginRequiredMixin, TemplateView):
    template_name = 'ipc/siderooms.html'

    def filter_statuses(self, statuses, flag):
        """
        Given a list of annotated bedstatus objects, filter them
        by those flagged with the IPCStatus.FLAGS boolean FLAG
        """
        flagged = []
        for status in statuses:
            if status.patient is None:
                continue

            ipcstatus = status.patient.ipcstatus_set.get()
            if getattr(ipcstatus, models.IPCStatus.FLAGS[flag]):
                flagged.append(status)
        return flagged

    def get_sex_count(self, statuses):
        """
        Given an iterable of STATUSES, return a count of male and female patients.
        """
        male = 0
        female = 0

        for bedstatus in statuses:
            if bedstatus.patient is None:
                continue
            demographics = bedstatus.patient.demographics()
            if demographics.sex == 'Male':
                male += 1
            if demographics.sex == 'Female':
                female += 1

        return male, female

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        side_rooms_statuses = list(BedStatus.objects.filter(
            hospital_site_code=k['hospital_code']).filter(
                Q(room__startswith='SR') | Q(bed__startswith='SR')
        ))

        isolation_status = []
        for isolated_bed in IsolatedBed.objects.filter(hospital_site_code=k['hospital_code']):
            bed_status = BedStatus.objects.filter(
                hospital_site_code=isolated_bed.hospital_site_code,
                ward_name=isolated_bed.ward_name,
                room=isolated_bed.room,
                bed=isolated_bed.bed,
            ).first()
            if bed_status:
                isolation_status.append(bed_status)

        isolation_ids = [i.id for i in side_rooms_statuses + isolation_status]

        # Patients with IPC flags not in siderooms or marked known open bays
        ipc_flags = [Q(**{f:True}) for f in [f"patient__ipcstatus__{k}" for k in models.IPCStatus.FLAGS.values()]]
        query = ipc_flags.pop()
        for f in ipc_flags:
            query |= f

        rogue_flagged_patients = BedStatus.objects.exclude(
            id__in=isolation_ids).exclude(patient__isnull=True).filter(
                hospital_site_code=k['hospital_code']).filter(query)
        rogue_ids = [i.id for i in rogue_flagged_patients]

        statuses = BedStatus.objects.filter(
            id__in=[i.id for i in rogue_flagged_patients]+isolation_ids

        ).exclude(ward_name='RF-Test').order_by('ward_name', 'bed')

        # Do this here in case we filter everything out later
        context['hospital_name'] = statuses[0].hospital_site_description

        for status in statuses:
            if not any([status.room.startswith('SR'), status.bed.startswith('SR')]):
                if status.id in rogue_ids:
                    status.is_rogue = True
                else:
                    status.is_open_bay = True

            if status.patient:
                ipc = status.patient.episode_set.filter(category_name='IPC').first()
                if ipc:
                    status.ipc_episode = ipc



        if k.get('flag'):
            context['flag'] = k['flag']
            statuses = self.filter_statuses(statuses, k['flag'])


        male, female = self.get_sex_count(statuses)
        context['male'] = male
        context['female'] = female

        wards = collections.defaultdict(list)

        for status in statuses:
            wards[status.ward_name].append(status)

        context['wards'] = {
            name[3:]: sorted(wards[name], key=sort_sideroom_beds) for name in
            reversed(sorted(wards.keys(), key=sort_rfh_wards))
            if not name in constants.WARDS_TO_EXCLUDE_FROM_SIDEROOMS
        }
        context['hospital_code'] = k['hospital_code']
        context['flags'] = list(models.IPCStatus.FLAGS.keys())
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


class IPCPortalSearchView(LoginRequiredMixin, View):

    def get(self, *args, **kwargs):
        results = find_patients_from_mrns([kwargs['mrn']])

        if len(results) == 0:
            return json_response(False)

        patient = next(iter(results.values()))
        demographics = patient.demographics()
        ipc_status = patient.ipcstatus_set.get()

        data = {
            'mrn'       : demographics.hospital_number,
            'name'      : demographics.name,
            'dob'       : demographics.date_of_birth,
            'is_flagged': ipc_status.is_flagged(),
            'flags'     : ipc_status.get_flags()
        }
        return json_response(data)

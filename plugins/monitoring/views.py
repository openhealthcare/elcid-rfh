"""
Views for the monitoring plugin
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from elcid.constants import (
    PATIENT_INFORMATION_SYNC_TIME, PATIENT_INFORMATION_UPDATE_COUNT
)
from plugins.imaging.constants import (
    IMAGING_LOAD_TIME_FACT,
    IMAGING_LOAD_CREATED_COUNT_FACT,
    IMAGING_LOAD_PATIENT_COUNT_FACT,
    IMAGING_COUNT_FACT
)

from plugins.appointments.constants import (
    APPOINTMENTS_LOAD_TIME_FACT,
    APPOINTMENTS_LOAD_CREATED_COUNT_FACT,
    APPOINTMENTS_LOAD_PATIENT_COUNT_FACT,
    APPOINTMENTS_COUNT_FACT
)

from plugins.admissions.constants import (
    ENCOUNTER_LOAD_MINUTES,
    TOTAL_ENCOUNTERS
)

from plugins.monitoring.models import Fact


def graph_data_for_label(label):
    """
    Given a label string as used by the Facts table, generate a
    datastructure that can be fed to a C3 chart.
    """
    ticks = ['x']
    series = [label]
    points = Fact.objects.filter(label=label).order_by('when')
    for point in points:
        try:
            series.append(point.val())
        except ValueError:
            continue
        ticks.append(point.when.strftime('%Y-%m-%d %H:%M:%S'))

    return [ticks, series]


class LabTimings(LoginRequiredMixin, TemplateView):
    template_name = 'monitoring/lab_timings.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        context['load_new_obs_data']    = graph_data_for_label('New Observations Per Load')
        context['sync_minutes_data']    = graph_data_for_label('48hr Sync Minutes')
        context['sync_48hr_count_data'] = graph_data_for_label('48hr Observations')
        context['patient_cohort_data']  = graph_data_for_label('Total Patients')
        context['total_obs_data']       = graph_data_for_label('Total Observations')

        return context


class PatientInformationLoadStats(LoginRequiredMixin, TemplateView):
    template_name = 'monitoring/patient_information_load_stats.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        context['patient_information_sync_time'] = graph_data_for_label(
            PATIENT_INFORMATION_SYNC_TIME
        )
        context['patient_information_updated'] = graph_data_for_label(
            PATIENT_INFORMATION_UPDATE_COUNT
        )
        return context


class ImagingLoadStats(LoginRequiredMixin, TemplateView):
    template_name = 'monitoring/imaging_load_stats.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        context['imaging_load_time_fact'] = graph_data_for_label(
            IMAGING_LOAD_TIME_FACT
        )
        context['imaging_load_created_count_fact'] = graph_data_for_label(
            IMAGING_LOAD_CREATED_COUNT_FACT
        )
        context['imaging_load_patient_count_fact'] = graph_data_for_label(
            IMAGING_LOAD_PATIENT_COUNT_FACT
        )
        context['imaging_count_fact'] = graph_data_for_label(
            IMAGING_COUNT_FACT
        )
        return context


class AppointmentLoadStats(LoginRequiredMixin, TemplateView):
    template_name = 'monitoring/appointment_load_stats.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        context['appointments_load_time_fact'] = graph_data_for_label(
            APPOINTMENTS_LOAD_TIME_FACT
        )
        context['appointments_load_created_count_fact'] = graph_data_for_label(
            APPOINTMENTS_LOAD_CREATED_COUNT_FACT
        )
        context['appointments_load_patient_count_fact'] = graph_data_for_label(
            APPOINTMENTS_LOAD_PATIENT_COUNT_FACT
        )
        context['appointments_count_fact'] = graph_data_for_label(
            APPOINTMENTS_COUNT_FACT
        )
        return context


class AdmissionLoadStats(LoginRequiredMixin, TemplateView):
    template_name = 'monitoring/admission_load_stats.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        context['encounter_load_time_fact'] = graph_data_for_label(
            ENCOUNTER_LOAD_MINUTES
        )
        context['encounter_count_fact'] = graph_data_for_label(
            TOTAL_ENCOUNTERS
        )
        return context


class SystemStats(  LoginRequiredMixin, TemplateView):
    template_name = 'monitoring/system_stats.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        context['back_up_size'] = graph_data_for_label('Backup size (GB)')
        context['disk_usage']   = graph_data_for_label('Disk Usage Percentage')
        return context

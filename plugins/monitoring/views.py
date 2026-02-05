"""
Views for the monitoring plugin
"""
import datetime, json
from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from opal import models as omodels

from elcid.constants import (
    PATIENT_INFORMATION_SYNC_TIME, PATIENT_INFORMATION_UPDATE_COUNT
)
from elcid import models
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

from plugins.admissions import models as admission_models
from plugins.tb import models as tbmodels
from plugins.labtests import models as labmodels

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


class MetricsHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'metrics/home.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)

        context['patient_count'] = omodels.Patient.objects.count()
        context['episode_count'] = omodels.Episode.objects.count()

        note_count = models.MicrobiologyInput.objects.count()
        note_count += tbmodels.PatientConsultation.objects.count()

        context['note_count']  = note_count

        # context['test_count']        = labmodels.LabTest.objects.count()
        # context['observation_count'] = labmodels.Observation.objects.count()
        context['movement_count']    = admission_models.TransferHistory.objects.count()
        return context


class NoteListView(LoginRequiredMixin, TemplateView):
    template_name = 'metrics/note_list.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        fks = models.MicrobiologyInput.objects.values('reason_for_interaction_fk').distinct()

        context['reasons'] = omodels.Clinical_advice_reason_for_interaction.objects.filter(id__in=fks)

        return context

class AdviceActivityView(LoginRequiredMixin, TemplateView):
    """
    This is a generic version of the ICU activity dashboard
    """
    template_name = 'metrics/advice_activity.html'

    @property
    def start_date(self):
        return datetime.date(int(self.kwargs["year"]), 1, 1)

    @property
    def end_date(self):
        return datetime.date(int(self.kwargs["year"]) + 1, 1, 1)

    @property
    def weeks(self):
        result = []
        first_monday = None
        for i in range(7):
            first_monday = self.start_date - datetime.timedelta(i)
            if first_monday.isoweekday() == 1:
                break

        for i in range(52):
            if first_monday + datetime.timedelta(i * 7) < self.end_date:
                start = first_monday + datetime.timedelta(i * 7)
                end = first_monday + datetime.timedelta((i + 1) * 7)
                result.append((start, end))
            else:
                break
        return result


    @property
    def menu_years(self):
        minimum_year = 2020
        current_year = datetime.date.today().year
        result = []
        for i in range(6):
            start_year = current_year - i
            end_year = current_year - i + 1
            if start_year < minimum_year:
                break

            count = models.MicrobiologyInput.objects.filter(
                reason_for_interaction_fk=self.kwargs['reason'],
                when__lte=datetime.date(start_year, 12, 31),
                when__gte=datetime.date(start_year, 1, 1)
            ).count()

            if count > 0:
                result.append((start_year, end_year,))

        result.reverse()
        return result

    def get_notes_by_user(self, notes):
        """
        Return a dict of notes grouped by user
        """
        minimum = 50
        by_user = defaultdict(int)

        for note in notes:
            by_user[note.initials] += 1

        result = dict()
        below = 0

        for k, v in by_user.items():
            if v < minimum:
                below += 1
            else:
                result[k] = v

        result = dict(sorted(
            result.items(), key=lambda x: x[1], reverse=True
        ))
        result[f"Other (<{minimum})"] = below
        return result

    def weekly_note_count(self, notes):
        """
        For a period of time, count note entries and group them
        by week. Create a datastructure that can be fed into C3
        """

        by_week = defaultdict(list)

        for note in notes:
            for start_week, end_week in self.weeks:
                if note.when.date() >= start_week:
                    if note.when.date() < end_week:
                        by_week[start_week].append(note)

        count = dict()

        for start, _ in self.weeks:
            notes = by_week.get(start, [])
            if len(notes) == 0:
                count[start] = 0
            else:
                whens = [i.when for i in notes]
                count[start] = len(whens)

        return {
            "x_axis": json.dumps(
                [f"{i.strftime('%d/%m')}-{b.strftime('%d/%m')}" for i, b in self.weeks]
            ),
            "vals": json.dumps(
                [
                    ["count"] + list(count.values()),
                ]
            ),
        }

    def get_context_data(self, *a, **kw):
        context = super(AdviceActivityView, self).get_context_data(*a, **kw)
        reason = self.kwargs['reason']
        notes = models.MicrobiologyInput.objects.filter(
            reason_for_interaction_fk_id=reason,
            when__gte=self.start_date,
            when__lte=self.end_date
        ).select_related('episode')
        episodes = set([n.episode for n in notes])
        patients = set([e.patient for e in episodes])

        context['year'] = self.kwargs['year']
        context['note_count'] = notes.count()
        context['patient_count'] = len(patients)
        context['notes_by_user'] = self.get_notes_by_user(notes)
        context['weekly_notes'] = self.weekly_note_count(notes)

        return context

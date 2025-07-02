"""
Views for the ICU plugin
"""
from collections import defaultdict
import datetime
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from opal.models import (
    Episode, Clinical_advice_reason_for_interaction, Patient
)

from elcid.episode_categories import InfectionService
from elcid.models import MicrobiologyInput
from plugins.admissions.models import BedStatus
from plugins.covid.models import CovidPatient
from plugins.epma.utils import get_anti_infectives_for_patient

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

    def get_anti_infectives(self, patient):
        """
        Given a PATIENT, return med orders that are in the category 'anti-infectives'
        """
        return get_anti_infectives_for_patient(patient, statuses=['Ordered'])

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
                'infection_note' : episode.infectionservicenote_set.get().text,
                'anti_infectives': self.get_anti_infectives(patient)
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


class ICUActivityView(LoginRequiredMixin, TemplateView):
    template_name = 'icu/activity.html'

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
        For a period of time, count ICU Round entries and group them
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
        context = super(ICUActivityView, self).get_context_data(*a, **kw)
        icu_round_reason = Clinical_advice_reason_for_interaction.objects.get(
            name=MicrobiologyInput.ICU_REASON_FOR_INTERACTION
        )
        notes = MicrobiologyInput.objects.filter(
            reason_for_interaction_fk_id=icu_round_reason.id,
            when__gte=self.start_date,
            when__lte=self.end_date
        ).select_related('episode')
        episodes = set([n.episode for n in notes])
        patients = set([e.patient for e in episodes])

        context['yer'] = self.kwargs['year']
        context['note_count'] = notes.count()
        context['patient_count'] = len(patients)
        context['notes_by_user'] = self.get_notes_by_user(notes)
        context['weekly_notes'] = self.weekly_note_count(notes)

        return context

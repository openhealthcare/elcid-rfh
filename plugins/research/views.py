"""
Views for the research plugin
"""
from collections import defaultdict
import csv
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.http import HttpResponse

from plugins.research import models
from plugins.research.studies import get_study_class


class ResearchHomeView(LoginRequiredMixin, TemplateView):
    """
    The root page for this module
    """
    template_name = 'research/home.html'

    def get_context_data(self, *args, **kwargs):
        """
        Prepare data for the Research module overviwe.
        """
        context = super().get_context_data(*args, **kwargs)

        context['study_count']       = models.Study.objects.filter(archived=False).count()
        context['participant_count'] = models.StudyParticipant.objects.filter(study__archived=False).count()

        return context


class StudyListView(LoginRequiredMixin, TemplateView):
    """
    List view for research studies
    """
    template_name = 'research/study_list.html'

    def get_context_data(self, *args, **kwargs):
        """
        Prepare data for the study list page
        """
        context = super().get_context_data(*args, **kwargs)

        context['studies'] = models.Study.objects.filter(archived=False)

        return context


class StudyDetailView(LoginRequiredMixin, TemplateView):
    """
    Detail view for a single study
    """

    _template_name = 'research/study_detail.html'

    @property
    def template_name(self, *args, **kwargs):
        return self.get_template_name()

    def get_template_name(self, *args, **kwargs):
        """
        Check to see if it is overriden
        """
        print('called')
        study = models.Study.objects.get(id=self.request.GET['study_id'])
        customisables = get_study_class(study.name)
        if customisables.template_name:
            return customisables.template_name
        return self._template_name

    def get_sex_breakdown(self, patients):
        """
        Given a list of PATIENTs, return a breakdown of their sex
        """
        by_sex = defaultdict(int)
        for patient in patients:
            demographics = patient.demographics()
            if demographics.sex:
                by_sex[demographics.sex] += 1
            else:
                by_sex['Not Known'] += 1

        return by_sex

    def get_age_groups(self, patients):
        """
        Given a list of PATIENTS, return a breakdown of their
        ages suitable for display as a bar chart
        """
        groups = ["0-20", "21-40", "41-60", "61-80", ">80"]

        children = 0
        twenties = 0
        fourties = 0
        sixties = 0
        old = 0

        for patient in patients:
            age = patient.demographics().age

            if not age:
                continue

            if age < 21:
                children += 1
                continue

            if age < 41:
                twenties += 1
                continue

            if age < 61:
                fourties += 1
                continue

            if age < 81:
                sixties += 1
                continue

            if age > 80:
                old += 1

        count = [children, twenties, fourties, sixties, old]

        return {
            "x_axis": json.dumps(groups),
            "vals"  : json.dumps(
                [
                    ["count"] + count
                ]
            )
        }


    def get_context_data(self, *args, **kwargs):
        """
        Prepare data for the study detail page
        """
        context = super().get_context_data(*args, **kwargs)

        study        = models.Study.objects.get(id=self.request.GET['study_id'])

        participants = study.get_participants()
        patients     = [p.patient for p in participants]

        context['study'] = study
        context['participant_count'] = models.StudyParticipant.objects.filter(study=study).count()

        context['sexes']    = self.get_sex_breakdown(patients)
        context['age_groups'] = self.get_age_groups(patients)

        return context


class StudyAddParticipantsView(LoginRequiredMixin, TemplateView):
    """
    Detail view to add participants
    """
    template_name = 'research/study_add_participants.html'

    def get_context_data(self, *args, **kwargs):
        """
        Fetch study context
        """
        context = super().get_context_data(*args, **kwargs)

        study = models.Study.objects.get(id=self.request.GET['study_id'])

        context['study'] = study
        context['participant_count'] = models.StudyParticipant.objects.filter(study=study).count()

        return context


class StudyParticipantListView(LoginRequiredMixin, TemplateView):
    """
    Detail view for study participants
    """
    template_name = "research/study_participant_list.html"

    def get_context_data(self, *args, **kwargs):
        """
        Fetch study context
        """
        context = super().get_context_data(*args, **kwargs)

        study = models.Study.objects.get(id=self.request.GET['study_id'])

        context['study'] = study
        context['participant_count'] = models.StudyParticipant.objects.filter(study=study).count()

        return context


class StudyDownloadView(LoginRequiredMixin, View):
    """
    Download data for a study
    """
    def get(self, *args, **kwargs):
        """
        Build and return a study CSV
        """
        study = models.Study.objects.get(id=kwargs['study_id'])

        customisables = get_study_class(study.name)

        response = customisables.download(study)

        return response

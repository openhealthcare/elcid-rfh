"""
Views for the research plugin
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from plugins.research import models


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
    template_name = 'research/study_detail.html'

    def get_context_data(self, *args, **kwargs):
        """
        Prepare data for the study detail page
        """
        context = super().get_context_data(*args, **kwargs)

        study = models.Study.objects.get(id=self.request.GET['study_id'])

        context['study'] = study
        context['participant_count'] = models.StudyParticipant.objects.filter(study=study).count()

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

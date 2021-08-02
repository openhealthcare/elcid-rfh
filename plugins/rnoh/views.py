"""
Views for the RNOH Plugin
"""
from django.views.generic import TemplateView
from opal.models import Episode

from opal.models import Hospital

from plugins.rnoh.episode_categories import RNOHEpisode


class RNOHInpatientsView(TemplateView):
    template_name = 'rnoh/inpatients_list.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        rnoh_id = Hospital.objects.get(name='RNOH').pk

        episodes = Episode.objects.filter(
            category_name=RNOHEpisode.display_name
        ).filter(location__hospital_fk=rnoh_id)
        context['episodes'] = episodes
        return context

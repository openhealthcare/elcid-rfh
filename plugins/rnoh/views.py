"""
Views for the RNOH Plugin
"""
from collections import defaultdict
from django.views.generic import TemplateView
from opal.models import Episode

from opal.models import Hospital

from plugins.rnoh.constants import INDIVIDUAL_WARD_NAMES, GROUPED_WARD_NAMES
from plugins.rnoh.episode_categories import RNOHEpisode


class RNOHView(TemplateView):
    INDIVIDUAL_WARD_NAMES = INDIVIDUAL_WARD_NAMES


class UsefulNumbersView(RNOHView):
    template_name = 'rnoh/numbers.html'


class RNOHInpatientsView(RNOHView):
    template_name = 'rnoh/inpatients_list.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        rnoh_id = Hospital.objects.get(name='RNOH').pk

        episodes = Episode.objects.filter(
            category_name=RNOHEpisode.display_name
        ).filter(
            location__hospital_fk=rnoh_id
        ).exclude(
            location__ward_ft__isnull=True
        ).exclude(
            location__ward_ft=''
        ).exclude(
            location__ward_ft__in=INDIVIDUAL_WARD_NAMES
        ).order_by('-location__ward_ft', '-location__bed')

        grouped_episodes = defaultdict(list)
        for e in episodes:
            grouped_episodes[e.location_set.get().ward].append(e)

        wards = [(ward_name, grouped_episodes[ward_name]) for ward_name in GROUPED_WARD_NAMES]

        context['total_episodes'] = episodes.count()
        context['wards']          = wards
        context['list_name']      = 'RNOH Inpatients'
        return context


class RNOHWardListView(RNOHView):

    template_name = 'rnoh/virtual_wards_list.html'

    def get_context_data(self, *a, **k):
        context = super().get_context_data(*a, **k)
        rnoh_id = Hospital.objects.get(name='RNOH').pk

        episodes = Episode.objects.filter(
            category_name=RNOHEpisode.display_name
        )

        kwargs={
            'location__hospital_fk':rnoh_id,
            "patient__rnohteams__"+k['ward_name'].lower().replace('-', '_').replace(' ', '_'): True
        }
        episodes = episodes.filter(**kwargs)


        context['episodes'] = episodes

        context['list_name'] = [n for n in INDIVIDUAL_WARD_NAMES if n.lower() == k['ward_name']][0]
        return context

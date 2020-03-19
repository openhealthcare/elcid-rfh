from elcid.episode_serialization import serialize
from elcid.models import Demographics
from intrahospital_api.models import ExternalDemographics
from intrahospital_api import constants
from opal.core import patient_lists
from opal.models import Patient, Episode


class ReconcileDemographics(patient_lists.PatientList):
    comparator_service = "EpisodeAddedComparator"
    order = 50
    display_name = "Reconcile Demographics"
    slug = "reconcile_all_demographics"
    template_name = 'reconcile_list.html'
    schema = []

    @property
    def queryset(self):
        patients = Patient.objects.filter(demographics__external_system=None)
        episodes_id = []
        for patient in patients:
            episode = patient.episode_set.last()
            episodes_id.append(episode.id)
        return Episode.objects.filter(id__in=episodes_id)

    def to_dict(self, user):
        qs = super(ReconcileDemographics, self).get_queryset()
        return serialize(
            qs, user, subrecords=[Demographics, ExternalDemographics]
        )

    @classmethod
    def visible_to(klass, user):
        return user.profile.roles.filter(
            name=constants.UPDATE_DEMOGRAPHICS
        ).exists()

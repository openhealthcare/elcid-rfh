from elcid.patient_lists import serialised
from elcid.models import Demographics
from intrahospital_api.models import ExternalDemographics
from intrahospital_api import constants
from opal.core import patient_lists
from opal.models import Patient, Episode


class ReconcileDemographics(patient_lists.PatientList):
    display_name = "Reconcile Demographics"
    slug = "reconcile_demographics"
    template_name = 'reconcile_list.html'
    schema = []

    @property
    def queryset(self):
        patients = Patient.objects.filter(demographics__external_system=None)
        return Episode.objects.filter(patient__in=patients)

    def to_dict(self, user):
        qs = super(ReconcileDemographics, self).get_queryset()
        return serialised(
            qs, user, subrecords=[Demographics, ExternalDemographics]
        )

    @classmethod
    def visible_to(klass, user):
        return user.profile.roles.filter(
            name=constants.UPDATE_DEMOGRAPHICS
        ).exists()

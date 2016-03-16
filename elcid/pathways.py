from copy import copy

from django.db import transaction
from elcid.models import (
    Diagnosis, Line, Antimicrobial, Location, PrimaryDiagnosis,
    Infection, Procedure, Demographics, MicrobiologyInput, FinalDiagnosis,
    BloodCulture, Imaging
)
from opal.models import Patient
from pathway.pathways import Pathway, UnrolledPathway, Step, RedirectsToEpisodeMixin


class AddPatientPathway(RedirectsToEpisodeMixin, Pathway):
    title = "Add Patient"
    slug = 'add_patient'

    steps = (
        Step(
            template_url="/templates/pathway/find_patient_form.html",
            controller_class="FindPatientCtrl",
            title="Find Patient",
            icon="fa fa-user"
        ),
        Step(
            model=Location,
            controller_class="BloodCultureLocationCtrl",
            template_url="/templates/pathway/blood_culture_location.html"
        ),
    )

    def save(self, data, user):
        episode = super(AddPatientPathway, self).save(data, user)

        # TODO: This should be refactored into the relevant step
        tagging = data["tagging"]
        episode.set_tag_names(tagging, user)
        return episode


class DemographicsStep(Step):
    def save(self, data, user, **kw):
        update_info = copy(data.get(self.model.get_api_name(), None))
        if 'consistency_token' not in update_info:
            return
        return super(DemographicsStep, self).save(data, user, **kw)


from django.core.urlresolvers import reverse

class CernerDemoPathway(UnrolledPathway):
    title = 'Cerner Powerchart Template'
    slug = 'cernerdemo'

    steps = (
        # TODO: Do we want to pass this like this ?
        # Wouldn't it be nicer if I could set it on the class?
        DemographicsStep(model=Demographics),
        Step(
            model=Location,
            controller_class="BloodCultureLocationCtrl",
            template_url="/templates/pathway/blood_culture_location.html",
        ),
        Step(
            model=Procedure,
            controller_class="MultiSaveCtrl",
            template_url="/templates/pathway/multi_save.html",
            model_form_url=reverse("form_template_view", kwargs=dict(model=Procedure)),
        ),
        PrimaryDiagnosis,
        Diagnosis,
        # Infection,
        Line,
        Antimicrobial,
        BloodCulture,
        Imaging,
        FinalDiagnosis,
        MicrobiologyInput,
        Step(model=Location, template_url='/templates/pathway/cernerletter.html')
    )

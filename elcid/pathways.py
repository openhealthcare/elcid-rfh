from elcid.models import (
    Diagnosis, Line, Antimicrobial, Location, PrimaryDiagnosis,
    Procedure, Demographics, MicrobiologyInput, FinalDiagnosis,
    BloodCulture, Imaging
)

from pathway.pathways import (
    Pathway, UnrolledPathway, Step, RedirectsToEpisodeMixin, DemographicsStep,
    MultSaveStep
)


class AddPatientPathway(RedirectsToEpisodeMixin, Pathway):
    display_name = "Add Patient"
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


class CernerDemoPathway(UnrolledPathway):
    display_name = 'Cerner Powerchart Template'
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
        MultSaveStep(model=Procedure),
        PrimaryDiagnosis,
        MultSaveStep(model=Diagnosis),
        # Infection,
        MultSaveStep(model=Line),
        MultSaveStep(model=Antimicrobial),
        MultSaveStep(model=BloodCulture),
        MultSaveStep(model=Imaging),
        FinalDiagnosis,
        MultSaveStep(model=MicrobiologyInput),
        Step(model=Location, template_url='/templates/pathway/cernerletter.html')
    )

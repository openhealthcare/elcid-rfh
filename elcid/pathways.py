from elcid.models import (
    Diagnosis, Line, Antimicrobial, Location, PrimaryDiagnosis,
    Procedure, Demographics, MicrobiologyInput, FinalDiagnosis,
    BloodCulture, Imaging
)

from pathway.pathways import (
    Pathway, UnrolledPathway, Step, RedirectsToEpisodeMixin,
    MultSaveStep, ModalPathway
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


class CernerDemoPathway(UnrolledPathway):
    display_name = 'Cerner Powerchart Template'
    slug = 'cernerdemo'

    steps = (
        # TODO: Do we want to pass this like this ?
        # Wouldn't it be nicer if I could set it on the class?
        Demographics,
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
        # MultSaveStep(model=BloodCulture),
        MultSaveStep(model=Imaging),
        FinalDiagnosis,
        MultSaveStep(model=MicrobiologyInput),
        Step(api_name="cerner_note", title="Clinical Note", icon="fa fa-envelope", template_url='/templates/pathway/cernerletter.html')
    )


class BloodCulturePathway(ModalPathway):
    display_name = 'Blood Culture'
    slug = 'blood_culture'
    template_url = "/templates/pathway/blood_culture_form_base.html"

    steps = (
        Step(
            model=BloodCulture,
            template_url="/templates/pathway/blood_culture_form.html",
            controller_class="BloodCultureLocationCtrl"
        ),
    )

    def save(self, data, user):
        """
            we're expecting all blood cultures for the episode
            in each post, so if they don't exist, delete them
        """
        blood_cultures = data.get("blood_culture", [])
        blood_culture_ids = [d["id"] for d in blood_cultures if d.get("id")]
        to_remove = self.episode.bloodculture_set.exclude(
            id__in=blood_culture_ids
        )

        to_remove.delete()

        return super(BloodCulturePathway, self).save(data, user)

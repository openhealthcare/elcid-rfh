from elcid import models


from pathway.pathways import (
    RedirectsToPatientMixin,
    RedirectsToEpisodeMixin,
    Step,
    PagePathway,
    WizardPathway,
    delete_others
)


class AddPatientPathway(RedirectsToEpisodeMixin, WizardPathway):
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
            model=models.Location,
            template_url="/templates/pathway/blood_culture_location.html"
        ),
    )


class CernerDemoPathway(RedirectsToPatientMixin, PagePathway):
    display_name = 'Cerner Powerchart Template'
    slug = 'cernerdemo'

    steps = (
        Step(
            template_url="/templates/pathway/cerner_letter_pathway.html",
            title="Cerner Letter",
            icon="fa fa-user",
            controller_class="BloodCulturePathwayFormCtrl"
        ),
    )

    def save(self, data, user):
        multi_saved_models = [
            models.Diagnosis,
            models.Infection,
            models.Line,
            models.Antimicrobial,
            # models.BloodCulture,
            models.Imaging,
            models.MicrobiologyInput
        ]
        for model in multi_saved_models:
            delete_others(data, model, self.patient, self.episode)
        return super(CernerDemoPathway, self).save(data, user)

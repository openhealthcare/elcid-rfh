from elcid import models
from lab import models as lmodels
from django.db import transaction
from django.conf import settings
from elcid import gloss_api


from pathway.pathways import (
    RedirectsToPatientMixin,
    RedirectsToEpisodeMixin,
    Step,
    PagePathway,
    WizardPathway,
    ModalPagePathway,
    delete_others
)


class SaveTaggingMixin(object):
    @transaction.atomic
    def save(self, data, user):
        tagging = data.pop("tagging", [])
        patient = super(SaveTaggingMixin, self).save(data, user)

        if tagging:
            tag_names = [n for n, v in list(tagging[0].items()) if v]
            if self.episode:
                episode = self.episode
            else:
                episode = patient.episode_set.last()
            episode.set_tag_names(tag_names, user)
        return patient


class AddPatientPathway(SaveTaggingMixin, RedirectsToEpisodeMixin, WizardPathway):
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
            template_url="/templates/pathway/blood_culture_location.html",
            controller_class="BloodCulturePathwayFormCtrl"
        ),
    )

    def save(self, data, *args, **kwargs):
        """
            saves the patient.

            if the patient already exists, create a new episode.

            if the patient doesn't exist and we're gloss enabled query gloss.

            if the patient isn't in gloss, or gloss is down, just create a
            new patient/episode
        """
        if settings.GLOSS_ENABLED:
            if not self.patient:
                demographics = data.get("demographics")
                hospital_number = demographics[0]["hospital_number"]
                created = gloss_api.patient_query(hospital_number)

                if created:
                    data.pop("demographics")
                    patient, episode = created
                    # nuke whatever is passed in in demographics as this will
                    # have been updated by gloss
                    data["demographics"] = [dict(
                        hospital_number=hospital_number,
                        consistency_token=patient.demographics_set.first().consistency_token
                    )]
                    self.patient_id = patient.id
                    self.episode_id = episode.id

            gloss_api.subscribe(hospital_number)

        return super(AddPatientPathway, self).save(data, *args, **kwargs)


class CernerDemoPathway(SaveTaggingMixin, RedirectsToPatientMixin, PagePathway):
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

    @transaction.atomic
    def save(self, data, user):
        multi_saved_models = [
            models.Diagnosis,
            models.Infection,
            models.Line,
            models.Antimicrobial,
            models.Imaging,
            models.MicrobiologyInput,
            lmodels.LabTest
        ]
        for model in multi_saved_models:
            delete_others(data, model, self.patient, self.episode)

        return super(CernerDemoPathway, self).save(data, user)


class BloodCulturePathway(ModalPagePathway):
    display_name = "Blood Culture"
    slug = "blood_culture"

    steps = (
        Step(
            template_url="/templates/pathway/blood_culture.html",
            title="Blood Culture",
            icon="fa fa-crosshairs",
            controller_class="BloodCulturePathwayFormCtrl"
        ),
    )

    @transaction.atomic
    def save(self, data, user):
        delete_others(data, lmodels.LabTest, self.patient, self.episode)
        return super(BloodCulturePathway, self).save(data, user)

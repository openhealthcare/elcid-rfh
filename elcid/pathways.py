from elcid import models
from opal import models as omodels
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
)
from pathway.steps import delete_others


class SaveTaggingMixin(object):
    @transaction.atomic
    def save(self, data, user, patient=None, episode=None):
        tagging = data.pop("tagging", [])
        patient, episode = super(SaveTaggingMixin, self).save(
            data, user, patient=patient, episode=episode
        )

        if tagging:
            tag_names = [n for n, v in list(tagging[0].items()) if v]
            episode.set_tag_names(tag_names, user)
        return patient, episode


class RemovePatientPathway(SaveTaggingMixin, PagePathway):
    icon = "fa fa-sign-out"
    display_name = "Remove"
    finish_button_text = "Remove"
    finish_button_icon = "fa fa-sign-out"
    modal_template = "pathway/modal_only_cancel.html"
    slug = "remove"
    steps = (
        Step(
            display_name="No",
            template="pathway/remove.html",
            step_controller="RemovePatientCtrl"
        ),
    )


class AddPatientPathway(SaveTaggingMixin, RedirectsToEpisodeMixin, WizardPathway):
    display_name = "Add Patient"
    slug = 'add_patient'

    steps = (
        Step(
            template="pathway/find_patient_form.html",
            step_controller="FindPatientCtrl",
            display_name="Find patient",
            icon="fa fa-user"
        ),
        Step(
            model=models.Location,
            template="pathway/blood_culture_location.html",
            step_controller="TaggingStepCtrl",
        ),
    )

    @transaction.atomic
    def save(self, data, user, patient=None, episode=None):
        """
            saves the patient.

            if the patient already exists, create a new episode.

            if the patient doesn't exist and we're gloss enabled query gloss.

            if the patient isn't in gloss, or gloss is down, just create a
            new patient/episode
        """
        if settings.GLOSS_ENABLED:
            demographics = data.get("demographics")
            hospital_number = demographics[0]["hospital_number"]

            if not patient:
                patient = omodels.Patient.objects.filter(
                    demographics__hospital_number=hospital_number
                )

            if patient:
                # the patient already exists

                # refreshes the saved patient
                gloss_api.patient_query(hospital_number)
                self.episode_id = patient.create_episode().id
            else:
                # the patient doesn't exist
                patient = gloss_api.patient_query(hospital_number)

                if patient:
                    # nuke whatever is passed in in demographics as this will
                    # have been updated by gloss
                    consistency_token = patient.demographics_set.first().consistency_token
                    data["demographics"] = [dict(
                        hospital_number=hospital_number,
                        consistency_token=consistency_token
                    )]
                    self.patient_id = patient.id
                    self.episode_id = patient.episode_set.get().id

            gloss_api.subscribe(hospital_number)

        return super(AddPatientPathway, self).save(
            data, user, patient=patient, episode=episode
        )


class CernerDemoPathway(SaveTaggingMixin, RedirectsToPatientMixin, PagePathway):
    display_name = 'Cerner Powerchart Template'
    slug = 'cernerdemo'

    steps = (
        models.Demographics,
        models.Location,
        Step(
            template="pathway/blood_culture.html",
            display_name="Blood Culture",
            icon="fa fa-crosshairs",
            step_controller="BloodCulturePathwayFormCtrl"
        ),
        models.Procedure,
        models.Diagnosis,
        models.Infection,
        models.Line,
        models.Antimicrobial,
        models.Imaging,
        models.FinalDiagnosis,
        models.MicrobiologyInput,
        Step(
            template="pathway/cernerletter.html",
            display_name="Clinical note",
            icon="fa fa-envelope"
        )
    )

    @transaction.atomic
    def save(self, data, user, patient=None, episode=None):
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
            delete_others(data, model, patient, episode)

        return super(CernerDemoPathway, self).save(
            data, user, patient=patient, episode=episode
        )


class BloodCulturePathway(PagePathway):
    display_name = "Blood Culture"
    slug = "blood_culture"

    steps = (
        Step(
            template="pathway/blood_culture.html",
            display_name="Blood Culture",
            icon="fa fa-crosshairs",
            step_controller="BloodCulturePathwayFormCtrl"
        ),
    )

    @transaction.atomic
    def save(self, data, user, patient=None, episode=None):
        delete_others(data, lmodels.LabTest, patient, episode)
        return super(BloodCulturePathway, self).save(
            data, user, patient=patient, episode=episode
        )

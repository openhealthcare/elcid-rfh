"""
Pathways for the TB service
"""
from django.db import transaction
from opal.core.pathway import pathways, HelpTextStep

from elcid import models
from elcid.pathways import IgnoreDemographicsMixin

from obs import models as obs_models

from plugins.tb import models as tb_models


class NewSubrecordStep(HelpTextStep):
    step_controller = "NewSubrecordStepCtrl"
    multiple = False


class ConditionalHelpStep(HelpTextStep):
    base_template = "pathway/steps/base_templates/conditional_help_step.html"

    def __init__(self, *args, **kwargs):
        self.condition = kwargs.pop("condition")
        super(ConditionalHelpStep, self).__init__(*args, **kwargs)


class ActiveTBTreatmentPathway(pathways.PagePathway):
    display_name = "Active TB Treatment"
    slug = "activate_tb_treatment"
    template = "pathway/consultation_base.html"

    steps = [
        HelpTextStep(
            template="pathway/steps/demographics_panel.html",
            icon="fa fa-user",
            display_name="Demographics",
            model=models.Demographics
        ),
        HelpTextStep(
            model=models.Diagnosis,
            template="pathway/steps/tb_diagnosis.html",
            step_controller="TBDiagnosis",
            help_text_template="pathway/steps/help_text/diagnosis.html"
        ),

        HelpTextStep(
            display_name="Treatment Plan",
            icon="fa fa-medkit",
            # base_template="pathway/steps/treatment_plan_base.html",
            # we use the base template instead
            template="pathway/steps/tb_treatment.html",
            step_controller="TBTreatmentCtrl",
            help_text_template="pathway/steps/help_text/tb_treatment.html",
        ),
    ]

    @transaction.atomic
    def save(self, data, user=None, **kwargs):
        stage = data.pop('stage')[0]
        patient, episode = super(ActiveTBTreatmentPathway, self).save(
            data, user=user, **kwargs
        )
        episode.set_stage(stage, user, data)
        episode.save()
        return patient, episode


class SymptomsPathway(IgnoreDemographicsMixin, pathways.PagePathway):
    """
    This pathway is used as a modal to edit symptoms for TB episodes.
    It uses the same template and controller as the symptoms step in the
    Initial Assessment pathway.
    """
    slug = "symptom_complex_pathway"
    display_name = models.SymptomComplex.get_display_name()
    icon = models.SymptomComplex.get_icon()
    steps = (
        pathways.Step(
            model=models.SymptomComplex,
            template="pathway/steps/symptom_complex.html",
            step_controller="TbSymptomComplexCrtl",
            multiple=False,
        ),
    )


class NationalityAndLanguage(pathways.PagePathway):
    """
    A pathway that asks for place of birth,
    immigration concerns and communication concerns
    """
    slug = "nationality_and_language"
    display_name = "Nationality And Language"
    icon = "fa fa-map-signs"
    steps = (
        pathways.Step(
            template="pathway/steps/nationality_and_language.html",
            display_name="Nationality and Language",
            icon="fa fa-file-image-o"
        ),
    )

    @transaction.atomic
    def save(self, data, user=None, episode=None, patient=None):
        # Demographics are loaded asynchronously on the backend
        # this does not update the client demographics (unlike lab tests)
        # as the demographics should not have changed.
        # however pathways throws an error on save for consistency tokens.
        # to get around this we need to update the demographics?

        if patient:
            our_demographics = patient.demographics_set.get()
            client_demographics = data.pop("demographics")
            our_demographics.birth_place = client_demographics[0]["birth_place"]
            our_demographics.save()
        return super().save(
            data, user=user, episode=episode, patient=patient
        )

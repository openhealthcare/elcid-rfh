"""
Pathways for the TB service
"""
from django.db import transaction
from opal.core.pathway import pathways, HelpTextStep

from elcid import models
from elcid.pathways import IgnoreDemographicsMixin

from plugins.obs import models as obs_models

from plugins.tb import models as tb_models


class NewSubrecordStep(HelpTextStep):
    step_controller = "NewSubrecordStepCtrl"
    multiple = False


class ConditionalHelpStep(HelpTextStep):
    base_template = "pathway/steps/base_templates/conditional_help_step.html"

    def __init__(self, *args, **kwargs):
        self.condition = kwargs.pop("condition")
        super(ConditionalHelpStep, self).__init__(*args, **kwargs)


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

            # We don't necessarily call update_from_dict on
            # pathway subrecords, only if they are editted,
            # so force removal of previous_mrn if we hit
            # the save method.
            patient.communinicationconsiderations_set.update(
                previous_mrn=None
            )
            patient.nationality_set.update(
                previous_mrn=None
            )

        result = super().save(
            data, user=user, episode=episode, patient=patient
        )
        return result

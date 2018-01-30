"""
Pathways for the TB service
"""
from django.db import transaction
from opal.core.pathway import pathways, Step

from elcid import models
from elcid.pathways import AddPatientPathway

from apps.tb.patient_lists import TbPatientList
from apps.tb import models as tb_models


class AddTbPatientPathway(AddPatientPathway):
    display_name = "Add TB Patient"
    slug = 'add_tb_patient'

    steps = (
        pathways.Step(
            template="pathway/rfh_find_patient_form.html",
            step_controller="RfhFindPatientCtrl",
            display_name="Find patient",
            icon="fa fa-user"
        ),
    )

    @transaction.atomic
    def save(self, data, user, patient=None, episode=None):
        patient, episode = super(AddTbPatientPathway, self).save(
            data, user=user, patient=patient, episode=episode
        )

        episode.set_tag_names([TbPatientList.tag], user)
        episode.category_name = "TB"
        episode.stage = "New Referral"
        episode.save()

        return patient, episode


class TBStep(Step):
    base_template = "pathway/steps/step_base.html"


class TBConsultationPathway(pathways.PagePathway):
    display_name = "Initial Assessment"
    slug = "initial_assessment"

    steps = [
        TBStep(
            template="pathway/steps/demographics_panel.html",
            icon="fa fa-user",
            display_name="Demographics"
        ),
        TBStep(model=models.ReferralRoute),
        TBStep(model=tb_models.ContactDetails),
        TBStep(
            model=models.SymptomComplex,
            template="pathway/steps/symptom_complex.html",
            step_controller="TbSymptomComplexCrtl",
            multiple=False,
        ),
        TBStep(
            model=tb_models.TBHistory,
            template="pathway/steps/tb_history.html",
        ),
        TBStep(model=tb_models.SocialHistory),
        # Antimicrobials need to be added
    ]

    @transaction.atomic
    def save(self, data, user, patient=None, episode=None):
        p, e = super(TBConsultationPathway, self).save(
            data, user, patient=patient, episode=episode
        )
        e.set_stage(e.category.NEW_REFERRAL, user, None)

        return p, e

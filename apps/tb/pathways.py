"""
Pathways for the TB service
"""
from django.db import transaction
from opal.core.pathway import pathways, HelpTextStep, Step

from elcid import models
from elcid.pathways import AddPatientPathway

from obs import models as obs_models

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


class TbStep(HelpTextStep):
    def get_help_text_template(self):
        entered = self.other_args.get("help_text_template", "").strip()

        if not entered and self.model:
            return "pathway/steps/help_text/{}.html".format(
                self.model.get_api_name()
            )


class NewSubrecordStep(HelpTextStep):
    step_controller = "NewSubrecordStepCtrl"
    multiple = False


class TBConsultationPathway(pathways.PagePathway):
    display_name = "Initial Assessment"
    slug = "initial_assessment"
    template = "pathway/consultation_base.html"

    steps = [
        TbStep(
            template="pathway/steps/demographics_birth_place.html",
            icon="fa fa-user",
            display_name="Demographics",
            model=models.Demographics
        ),
        TbStep(model=models.ReferralRoute),
        HelpTextStep(
            model=tb_models.ContactDetails,
            help_text="This will be pulled in from Cerner"
        ),
        HelpTextStep(
            model=tb_models.NextOfKin,
            help_text="This will be pulled in from Cerner"
        ),
        HelpTextStep(
            model=models.SymptomComplex,
            template="pathway/steps/symptom_complex.html",
            step_controller="TbSymptomComplexCrtl",
            multiple=False,
        ),
        TbStep(
            model=tb_models.TBHistory,
        ),
        HelpTextStep(
            model=tb_models.BCG,
        ),
        HelpTextStep(model=tb_models.SocialHistory),
        HelpTextStep(
            model=models.Antimicrobial,
            template="pathway/steps/drug_history.html"
        ),
        HelpTextStep(model=tb_models.Allergies),
        HelpTextStep(model=models.PastMedicalHistory),
        HelpTextStep(model=tb_models.Travel),
        NewSubrecordStep(
            model=obs_models.Observation,
            multiple=False
        ),
        NewSubrecordStep(
            model=tb_models.MantouxTestOne,
            multiple=False
        ),
        NewSubrecordStep(
            model=tb_models.MantouxTestTwo,
            multiple=False
        ),
        NewSubrecordStep(
            model=tb_models.PatientConsultation,
            multiple=False
        ),
    ]

    @transaction.atomic
    def save(self, data, user, patient=None, episode=None):
        p, e = super(TBConsultationPathway, self).save(
            data, user, patient=patient, episode=episode
        )
        e.set_stage(e.category.NEW_REFERRAL, user, None)

        return p, e


class ActiveTBTreatmentPathway(pathways.PagePathway):
    display_name = "Active TB Treatment"
    slug = "activate_tb_treatment"
    template = "pathway/consultation_base.html"

    steps = [
        TbStep(
            template="pathway/steps/demographics_panel.html",
            icon="fa fa-user",
            display_name="Demographics",
            model=models.Demographics
        ),
        TbStep(
            model=models.Diagnosis,
            template="pathway/steps/tb_diagnosis.html",
            step_controller="TBDiagnosis",
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

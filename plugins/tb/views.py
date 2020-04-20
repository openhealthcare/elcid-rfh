"""
Views for the TB Opal Plugin
"""
import datetime
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from plugins.tb.models import PatientConsultation
from django.views.generic import TemplateView
from opal.core.serialization import deserialize_datetime
from plugins.tb.utils import get_tb_summary_information

from plugins.tb.models import Treatment
from elcid.models import Diagnosis
from opal import views


class ClinicalAdvicePrintView(LoginRequiredMixin, DetailView):
    template_name = 'tb/clinical_advice.html'
    model = PatientConsultation


class AbstractLetterView(LoginRequiredMixin, DetailView):
    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        episode = self.object.episode
        patient = self.object.episode.patient
        ctx["demographics"] = patient.demographics()
        ctx["primary_diagnosis_list"] = episode.diagnosis_set.filter(
            category=Diagnosis.PRIMARY
        ).order_by("-date_of_diagnosis")

        ctx["secondary_diagnosis_list"] = episode.diagnosis_set.exclude(
            category=Diagnosis.PRIMARY
        ).order_by("-date_of_diagnosis")

        ctx["tb_medication_list"] = episode.treatment_set.filter(
            category=Treatment.TB
        )
        ctx["nationality"] = patient.nationality_set.first()
        ctx["other_medication_list"] = episode.treatment_set.exclude(
            category=Treatment.TB
        )
        ctx["communication_considerations"] = patient.communinicationconsiderations_set.get()
        ctx["results"] = get_tb_summary_information(patient)
        for result in ctx["results"].values():
            result["observation_datetime"] = deserialize_datetime(
                result["observation_datetime"]
            )
        ctx["travel_list"] = episode.travel_set.all()
        ctx["adverse_reaction_list"] = episode.adversereaction_set.all()
        ctx["past_medication_list"] = episode.antimicrobial_set.all()
        ctx["allergies_list"] = patient.allergies_set.all()
        ctx["imaging_list"] = episode.imaging_set.all()
        ctx["tb_history"] = patient.tbhistory_set.get()
        ctx["index_case_list"] = patient.indexcase_set.all()
        ctx["other_investigation_list"] = episode.otherinvestigation_set.all()
        consultation_datetime = self.object.when
        if consultation_datetime:
            obs = episode.observation_set.filter(
                datetime__date=consultation_datetime.date()
            ).last()
            if obs:
                ctx["weight"] = obs.weight
        return ctx


class InitialAssessment(AbstractLetterView):
    template_name = "tb/letters/initial_assessment.html"
    model = PatientConsultation

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        episode = self.object.episode
        patient = self.object.episode.patient
        ctx["referral"] = episode.referralroute_set.get()
        ctx["social_history"] = episode.socialhistory_set.get()

        ctx["symptom_complex_list"] = episode.symptomcomplex_set.all()
        # TODO this has to change

        ctx["patient"] = patient
        return ctx


class FollowUp(AbstractLetterView):
    template_name = "tb/letters/follow_up.html"
    model = PatientConsultation

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        episode = self.object.episode
        patient = self.object.episode.patient
        ctx["adverse_reaction_list"] = episode.adversereaction_set.all()
        return ctx


class AbstractModalView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["column"] = self.model
        return ctx


class PrimaryDiagnosisModal(AbstractModalView):
    template_name = "modals/primary_diagnosis.html"
    model = Diagnosis


class SecondaryDiagnosisModal(AbstractModalView):
    template_name = "modals/secondary_diagnosis.html"
    model = Diagnosis


class TbMedicationModal(AbstractModalView):
    template_name="modals/tb_medication.html"
    model = Treatment


class OtherMedicationModal(AbstractModalView):
    template_name = "modals/other_medication.html"
    model = Treatment

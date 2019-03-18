"""
Views for the TB Opal Plugin
"""

from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.tb.models import PatientConsultation
from apps.tb.utils import get_tb_summary_information


class ClinicalAdvicePrintView(LoginRequiredMixin, DetailView):
    template_name = 'tb/clinical_advice.html'
    model = PatientConsultation


class AbstractLetterView(LoginRequiredMixin, DetailView):
    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        episode = self.object.episode
        patient = self.object.episode.patient
        ctx["demographics"] = patient.demographics()
        ctx["diagnosis_list"] = episode.diagnosis_set.order_by("-date_of_diagnosis")
        ctx["past_medical_history_list"] = episode.pastmedicalhistory_set.all()
        ctx["tb_teatment_list"] = episode.treatment_set.all()
        ctx["adverse_reaction_list"] = episode.adversereaction_set.all()
        ctx["past_medication_list"] = episode.antimicrobial_set.all()
        ctx["allergies_list"] = patient.allergies_set.all()
        return ctx


class LatentNewPatientAssessment(AbstractLetterView):
    template_name = "tb/letters/latent_new_patient_assessment.html"
    model = PatientConsultation

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        episode = self.object.episode
        patient = self.object.episode.patient
        ctx["referral"] = episode.referralroute_set.get()
        ctx["communication_considerations"] = patient.communinicationconsiderations_set.get()
        ctx["social_history"] = episode.socialhistory_set.get()
        ctx["travel_list"] = episode.travel_set.all()

        ctx["symptom_complex_list"] = episode.symptomcomplex_set.all()
        # TODO this has to change

        ctx["imaging_list"] = episode.imaging_set.all()
        ctx["other_investigation_list"] = episode.otherinvestigation_set.all()
        obs = episode.observation_set.order_by("-datetime").last()
        if obs:
            ctx["weight"] = obs.weight
        ctx["patient"] = patient
        ctx["tb_history"] = patient.tbhistory_set.get()
        ctx["results"] = get_tb_summary_information(patient)
        return ctx


class FollowUpPatientAssessment(AbstractLetterView):
    template_name = "tb/letters/follow_up_patient_assessment.html"
    model = PatientConsultation

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        episode = self.object.episode
        patient = self.object.episode.patient
        ctx["results"] = get_tb_summary_information(patient)
        ctx["adverse_reaction_list"] = episode.adversereaction_set.all()

        obs = episode.observation_set.order_by("-datetime").last()
        if obs:
            ctx["weight"] = obs.weight

        return ctx


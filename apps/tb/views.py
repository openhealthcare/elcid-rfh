"""
Views for the TB Opal Plugin
"""

from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.tb.models import PatientConsultation


class ClinicalAdvicePrintView(LoginRequiredMixin, DetailView):
    template_name = 'tb/clinical_advice.html'
    model = PatientConsultation


class LatentNewPatientAssessment(LoginRequiredMixin, DetailView):
    template_name = "tb/letters/latent_new_patient_assessment.html"
    model = PatientConsultation

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        episode = self.object.episode
        patient = self.object.episode.patient
        ctx["demographics"] = patient.demographics()
        ctx["referral"] = episode.referralroute_set.get()
        ctx["communication_considerations"] = patient.communinicationconsiderations_set.get()
        ctx["social_history"] = episode.socialhistory_set.get()
        ctx["past_medical_history_list"] = episode.pastmedicalhistory_set.all()

        # TODO this has to change
        ctx["past_medication_list"] = episode.antimicrobial_set.all()
        ctx["allergies_list"] = patient.allergies_set.all()
        ctx["diagnosis_list"] = episode.diagnosis_set.order_by("-date_of_diagnosis")
        obs = episode.observation_set.order_by("-datetime").last()
        if obs:
            ctx["weight"] = obs.weight
        ctx["patient"] = patient
        ctx["tb_history"] = patient.tbhistory_set.get()
        return ctx

class FollowUpPatientAssessment(LoginRequiredMixin, DetailView):
    template_name = "tb/letters/follow_up_patient_assessment.html"
    model = PatientConsultation

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        episode = self.object.episode
        patient = self.object.episode.patient
        ctx["demographics"] = patient.demographics()
        ctx["current_teatment_list"] = episode.treatment_set.all()
        ctx["diagnosis_list"] = episode.diagnosis_set.order_by("-date_of_diagnosis")
        ctx["past_medical_history_list"] = episode.pastmedicalhistory_set.all()

        obs = episode.observation_set.order_by("-datetime").last()
        if obs:
            ctx["weight"] = obs.weight

        return ctx


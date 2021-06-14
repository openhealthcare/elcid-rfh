"""
Views for the TB Opal Plugin
"""
import datetime
from collections import defaultdict
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView
from opal.core.serialization import deserialize_datetime
from elcid.models import Diagnosis, Demographics
from plugins.appointments.models import Appointment
from plugins.labtests import models as labtest_models

from plugins.tb import episode_categories, constants
from plugins.tb import models
from plugins.tb.models import PatientConsultation
from plugins.tb.models import Treatment
from plugins.tb.utils import get_tb_summary_information


class ClinicalAdvicePrintView(LoginRequiredMixin, DetailView):
    template_name = "tb/clinical_advice.html"
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

        ctx["tb_medication_list"] = episode.treatment_set.filter(category=Treatment.TB)
        ctx["nationality"] = patient.nationality_set.first()
        ctx["other_medication_list"] = episode.treatment_set.exclude(
            category=Treatment.TB
        )
        ctx[
            "communication_considerations"
        ] = patient.communinicationconsiderations_set.get()
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


class NurseLetter(AbstractLetterView):
    template_name = "tb/letters/nurse_letter.html"
    model = PatientConsultation


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
    template_name = "modals/tb_medication.html"
    model = Treatment


class OtherMedicationModal(AbstractModalView):
    template_name = "modals/other_medication.html"
    model = Treatment


class ClinicList(LoginRequiredMixin, ListView):
    template_name = "tb/clinic_list.html"

    def get_queryset(self, *args, **kwargs):
        today = timezone.now().date()
        until = today + datetime.timedelta(30)
        appointment_types = constants.TB_APPOINTMENT_CODES
        return Appointment.objects.filter(
            derived_appointment_type__in=appointment_types
        ).filter(
           start_datetime__gte=today,
           start_datetime__lte=until
        ).exclude(
           status_code="Canceled"
        ).order_by(
           "start_datetime"
        ).prefetch_related(
            'patient__episode_set'
        )

    def get_patient_id_to_recent_consultation(self, patient_ids):
        """
        return patient id to the most patient consultation
        """
        patient_id_to_consultation = {}
        consultations = PatientConsultation.objects.filter(
            episode__patient_id__in=patient_ids
        )
        consultations = (
            consultations.filter(
                episode__category_name=episode_categories.TbEpisode.display_name
            )
            .order_by("when")
            .select_related("episode")
        )
        for consultation in consultations:
            patient_id_to_consultation[consultation.episode.patient_id] = consultation

        return patient_id_to_consultation

    def get_patient_id_to_demographics(self, patient_ids):
        demographics = Demographics.objects.filter(patient_id__in=patient_ids)
        return {demographic.patient_id: demographic for demographic in demographics}

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["rows_by_date"] = defaultdict(list)
        patient_ids = set([i.patient_id for i in ctx["object_list"]])
        patient_id_to_demographics = self.get_patient_id_to_demographics(patient_ids)
        patient_id_to_consultation = self.get_patient_id_to_recent_consultation(
            patient_ids
        )
        for admission in ctx["object_list"]:
            tb_episode = None
            for ep in admission.patient.episode_set.all():
                if ep.category_name == episode_categories.TbEpisode.display_name:
                    tb_episode = ep

            # there should always be a TB episode but if there isn't skip it
            if not tb_episode:
                continue

            demographics = patient_id_to_demographics.get(admission.patient_id)
            recent_consultation = patient_id_to_consultation.get(admission.patient_id)
            ctx["rows_by_date"][admission.start_datetime.date()].append(
                (
                    admission,
                    demographics,
                    tb_episode,
                    recent_consultation,
                )
            )
        ctx["rows_by_date"] = dict(ctx["rows_by_date"])
        return ctx


class PrintConsultation(LoginRequiredMixin, DetailView):
    model = models.PatientConsultation
    template_name = "tb/patient_consultation_print.html"


class MDTList(LoginRequiredMixin, ListView):
    start_datetime = datetime.datetime(2021, 4, 17)
    end_datetime = datetime.datetime(2021, 5, 5)
    test_type = "AFB : CULTURE"
    observation_names = [
        "TB: Culture Result", "TB PCR", "AFB Smear"
    ]
    model = labtest_models.LabTest
    template_name = "tb/mdt_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset()
        a_year_ago = datetime.date.today() - datetime.timedelta(365)
        return qs.filter(
            test_name=self.test_type
        ).filter(
            datetime_ordered__gt=a_year_ago
        ).order_by(
            "-datetime_ordered"
        ).prefetch_related(
            'observation_set'
        )

    def get_observation_result(self, lt):
        result = {}
        for obs in lt.observation_set.all():
            if obs.observation_name in self.observation_names:
                if obs.observation_name == "TB: Culture Result":
                    if not obs.observation_value:
                        continue
                    if obs.observation_value == "AFB culture to follow.":
                        continue
                result[obs.observation_name] = obs.observation_value
        return result

    def get_site(self, lt):
        site = lt.site
        splitted = site.split("^")
        if len(splitted) == 1:
            return site
        return splitted[1].split("&")[0]

    def get_patient_id_to_demographics(self, lab_tests):
        patient_ids = set([i.patient_id for i in lab_tests])
        demographics = Demographics.objects.filter(patient_id__in=patient_ids)
        result = {}
        for demo in demographics:
            result[demo.patient_id] = demo
        return result

    def get_patient_id_to_lab_dicts(self, lab_tests):
        patient_ids_to_lab_test_dict = defaultdict(list)
        for lab_test in lab_tests:
            results = self.get_observation_result(lab_test)
            if not results:
                continue
            location = ""
            if "L" in lab_test.lab_number:
                location = "RFH"
            elif "K" in lab_test.lab_number:
                location = "Barnet"
            patient_ids_to_lab_test_dict[lab_test.patient_id].append({
                "site": self.get_site(lab_test),
                "location": location,
                "lab_number": lab_test.lab_number,
                "ordered": lab_test.datetime_ordered.date(),
                "results": results
            })
        result = {}
        for patient_id, lab_test_dicts in patient_ids_to_lab_test_dict.items():
            result[patient_id] = sorted(
                lab_test_dicts, key=lambda x: x["ordered"], reverse=True
            )
        return result

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data()
        lab_tests = ctx["object_list"]
        patient_id_to_demographics = self.get_patient_id_to_demographics(lab_tests)
        patient_id_to_lab_test_dicts = self.get_patient_id_to_lab_dicts(lab_tests)

        patient_id_lab_test_dicts = sorted(
            patient_id_to_lab_test_dicts.items(),
            key=lambda lab_test_dicts: lab_test_dicts[1][0]["ordered"],
            reverse=True
        )
        rows = []
        for patient_id, lab_test_dicts in patient_id_lab_test_dicts:
            demographics = patient_id_to_demographics[patient_id]
            rows.append((demographics, lab_test_dicts,))
        ctx["rows"] = rows
        return ctx

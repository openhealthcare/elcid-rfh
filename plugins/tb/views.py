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
from opal.models import PatientConsultationReasonForInteraction
from elcid.models import Diagnosis, Demographics
from plugins.appointments.models import Appointment
from opal.models import Patient
from plugins.tb import episode_categories, constants, models
from plugins.tb.models import PatientConsultation, Treatment
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


class NurseLetter(LoginRequiredMixin, DetailView):
    template_name = "tb/letters/nurse_letter.html"
    model = PatientConsultation

    def get_lab_test_observations(self, patient, clinical_advice, test_name, observation_names):
        """
        Return a lab test where at least one of the observations for
        that day are numeric
        """
        if not clinical_advice.when:
            return []
        last_lab_tests = patient.lab_tests.filter(
            test_name=test_name
        ).filter(
            datetime_ordered__lt=clinical_advice.when
        ).prefetch_related(
            'observation_set'
        ).order_by("-datetime_ordered").reverse()
        test = None
        for last_lab_test in last_lab_tests:
            for observation in last_lab_test.observation_set.all():
                if observation.observation_name in observation_names:
                    test = last_lab_test
                    break
        if not test:
            return []
        observations = last_lab_test.observation_set.all()
        return [
            i for i in observations if i.observation_name in observation_names
        ]

    def get_bloods(self, patient, clinical_advice):
        """
        Returns the most recent observations before the clincial
        advice for liver, urea, CRP, and full blood count observations.
        """
        result = []

        # Liver observations
        result.extend(self.get_lab_test_observations(
            patient,
            clinical_advice,
            "LIVER PROFILE",
            ["ALT", "AST", "Albumin", "Alkaline Phosphatase", "Total Bilirubin"]
        ))

        # Urea observations
        result.extend(self.get_lab_test_observations(
            patient,
            clinical_advice,
            "UREA AND ELECTROLYTES",
            ["Creatinine", "Potassium", "Sodium", "Urea"]
        ))

        # CRP
        result.extend(self.get_lab_test_observations(
            patient,
            clinical_advice,
            "C REACTIVE PROTEIN",
            ["C Reactive Protein"]
        ))

        # Full blood count
        result.extend(self.get_lab_test_observations(
            patient,
            clinical_advice,
            "C FULL BLOOD COUNT",
            ["Hb", "WBC", "Platelets"]
        ))
        return result

    def get_observations(self, patient_consultation):
        """
        These are observations
        as in obs.models, ie weight and temperature
        rather than labtests.models.Observation.

        Return the most recent populated observation
        of todays date.
        """
        # field to units
        obs_fields = {
            "bp_systolic",
            "bp_diastolic",
            "pulse",
            "resp_rate",
            "sp02",
            "temperature",
            "height",
            "weight",
        }
        result = {}
        if not patient_consultation.when:
            return result
        todays_obs = patient_consultation.episode.observation_set.filter(
            datetime__date=patient_consultation.when.date()
        ).order_by("datetime")
        if not todays_obs:
            return result
        for obs_field in obs_fields:
            for observation in todays_obs:
                obs_val = getattr(observation, obs_field)
                if obs_val is not None:
                    break
            if obs_val:
                result[obs_field] = str(obs_val).rsplit('.0', 1)[0]
        return result

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        episode = ctx["object"].episode
        ctx["patient"] = episode.patient
        ctx["bloods"] = self.get_bloods(episode.patient, ctx["object"])
        if not ctx["bloods"]:
            ctx["bloods_normal"] = False
        else:
            # are all the bloods within reference range
            ctx["bloods_normal"] = not any([
                i for i in ctx["bloods"] if i.is_outside_reference_range()
            ])
        ctx["diagnosis"] = episode.diagnosis_set.filter(
            category=Diagnosis.PRIMARY
        ).first()
        tb_treatments = episode.treatment_set.filter(
            category=Treatment.TB
        )
        tb_treatments = sorted(
            [i for i in tb_treatments if i.start_date],
            key=lambda x: x.start_date
        )
        if tb_treatments:
            ctx["treatment_commenced"] = tb_treatments[0].start_date

        current_treatments = [i for i in tb_treatments if not i.end_date]
        ctx["current_treatments"] = ", ".join([i.drug for i in current_treatments])
        adverse_reaction = episode.adversereaction_set.first()
        if adverse_reaction:
            ctx["adverse_reaction"] = adverse_reaction.details
        ctx["observations"] = self.get_observations(ctx["object"])
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
    template_name = "modals/tb_medication.html"
    model = Treatment


class OtherMedicationModal(AbstractModalView):
    template_name = "modals/other_medication.html"
    model = Treatment


class AbstractTBAppointmentList(LoginRequiredMixin, ListView):
    """
    An abstract class that will display a bunch of TB appointments in
    a list.

    Expects:
      name to be defined, on the view, ie the name of the list
      get_queryset to return a bunch of appointments
    """
    def get_queryset(self, *args, **kwargs):
        raise NotImplementedError()

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


class ClinicList(AbstractTBAppointmentList):
    template_name = "tb/tb_patient_list.html"
    name = "TB Clinic List"

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


class Last30Days(AbstractTBAppointmentList):
    template_name = "tb/tb_patient_list.html"
    name = "Clinic History: last 30 days"

    def get_queryset(self, *args, **kwargs):
        today = timezone.now().date()
        until = today - datetime.timedelta(30)
        appointment_types = constants.TB_APPOINTMENT_CODES
        appointments = Appointment.objects.filter(
            derived_appointment_type__in=appointment_types
        ).filter(
           start_datetime__lte=today,
           start_datetime__gte=until
        ).exclude(
           status_code="Canceled"
        ).order_by(
           "start_datetime"
        ).prefetch_related(
            'patient__episode_set'
        )
        return sorted(appointments, key=lambda x: x.start_datetime.date())


class PrintConsultation(LoginRequiredMixin, DetailView):
    model = models.PatientConsultation
    template_name = "tb/patient_consultation_print.html"


class MDTList(LoginRequiredMixin, TemplateView):
    template_name = "tb/mdt_list.html"
    BARNET = "BARNET"
    RFH = "RFH"
    SITES = [RFH, BARNET]
    POSITIVE = "POSITIVE"
    RESULTED = "RESULTED"
    STATUSES = [POSITIVE, RESULTED]

    ALL_OBS = "ALL_OBS"
    CULTURE = "CULTURE"
    SMEAR = "SMEAR"
    PCR = "PCR"
    REF_LAB = "REF_LAB"

    TB_OBSERVATIONS = {
        ALL_OBS: [
            models.TBPCR,
            models.AFBSmear,
            models.AFBCulture,
            models.AFBRefLib,
        ],
        CULTURE: [models.AFBCulture],
        SMEAR: [models.AFBSmear],
        REF_LAB: [models.AFBRefLib],
        PCR: [models.TBPCR],
    }

    def patients_to_rows(self, patients):
        obs_models = self.TB_OBSERVATIONS[self.request.GET.get("obs_type")]
        obs_status = self.request.GET['status']
        filter_kwargs = {'patient__in': patients}
        if obs_status == self.POSITIVE:
            filter_kwargs['positive'] = True
        else:
            filter_kwargs['pending'] = False

        patient_id_to_obs = defaultdict(list)
        for obs_model in obs_models:
            qs = obs_model.objects.filter(**filter_kwargs)
            for obs in qs:
                patient_id_to_obs[obs.patient_id].append(obs)

        patient_id_to_obs = {
            patient_id: sorted(obs, key=lambda x: x.reported_datetime, reverse=True)
            for patient_id, obs in patient_id_to_obs.items()
        }

        patient_consultations = models.PatientConsultation.objects.filter(
            episode__patient__in=patients
        ).select_related('episode')
        patient_id_to_consultations = defaultdict(list)
        for pc in patient_consultations:
            patient_id_to_consultations[pc.episode.patient_id].append(pc)

        # Make sure the list is sorted by the most recent observation
        patients = sorted(
            patients, key=lambda x: patient_id_to_obs[x.id][0].reported_datetime
        )

        result = []
        for patient in patients:
            result.append(
                self.patient_to_row(
                    patient,
                    patient_id_to_obs[patient.id],
                    patient_id_to_consultations[patient.id]
                )
            )
        return result

    @property
    def end_date(self):
        today = datetime.date.today()
        for i in range(7):
            some_date = today + datetime.timedelta(i)
            if some_date.isoweekday() == 2:
                return some_date

    @property
    def start_date(self):
        return self.end_date - datetime.timedelta(21)

    def title(self):
        obs_type = self.request.GET.get("obs_type")
        if obs_type == self.ALL_OBS:
            obs_type = "tests"
        elif obs_type == self.REF_LAB:
            obs_type = "ref lab reports"
        elif obs_type == self.PCR:
            obs_type = "PCR tests"
        else:
            obs_type = f"{obs_type.lower()} tests"

        status = self.request.GET.get("status").lower()
        from_dt = self.start_date.strftime("%-d %b %Y")
        title = f"Patients with {status} {obs_type} reported after {from_dt}"
        return title.replace("  ", " ")

    def get_patients(self):
        filter_args = {
            "reported_datetime__gte": self.start_date,
            "pending": False
        }
        if self.request.GET.get("status").upper() == self.POSITIVE:
            filter_args["positive"] = True
        if self.request.GET["site"].upper() == self.BARNET:
            filter_args["lab_number__contains"] = "K"
        else:
            filter_args["lab_number__contains"] = "L"
        tb_obs_models = self.TB_OBSERVATIONS[self.request.GET.get("obs_type")]
        patient_ids = set()
        for tb_obs_model in tb_obs_models:
            patient_ids = patient_ids.union(tb_obs_model.objects.filter(
                **filter_args
            ).values_list('patient_id', flat=True))
        return Patient.objects.filter(
            id__in=patient_ids
        ).prefetch_related(
            'demographics_set',
            'episode_set',
            'appointments'
        ).distinct()

    def filter_obs(self, obs):
        # For a given date only show the most important test on that date
        # Ref libs are most important, then cultures, then smears then pcrs.
        importance = {
            models.TBPCR.OBSERVATION_NAME: 0,
            models.AFBSmear.OBSERVATION_NAME: 1,
            models.AFBCulture.OBSERVATION_NAME: 2,
            models.AFBRefLib.OBSERVATION_NAME: 3,
        }
        by_date = {}
        for ob in obs:
            reported_date = ob.reported_datetime.date()
            if reported_date not in by_date:
                by_date[reported_date] = ob
            else:
                existing_ob = by_date[reported_date]
                existing_importance = importance[existing_ob.OBSERVATION_NAME]
                ob_importance = importance[ob.OBSERVATION_NAME]
                if existing_importance < ob_importance:
                    by_date[reported_date] = ob
        return by_date.values()

    def patient_to_row(self, patient, obs, patient_consultations):
        demographics = patient.demographics_set.all()[0]
        tb_category = episode_categories.TbEpisode.display_name
        tb_episodes = [i for i in patient.episode_set.all() if i.category_name == tb_category]
        if tb_episodes:
            episode = tb_episodes[0]

        obs = [
            (i.reported_datetime, 'obs', i) for i in self.filter_obs(obs)
        ]

        # Only include TB appointmments
        appointments = [
            i for i in patient.appointments.all()
            if i.derived_appointment_type in constants.TB_APPOINTMENT_CODES and i.start_datetime
        ]

        # Only show the first appointment or future appointments
        appointments = [
            i for i in patient.appointments.all() if i.derived_appointment_type == "Thoracic TB New" or i.start_datetime > timezone.now()
        ]

        appointments = [
            (i.start_datetime, "appointment", i,) for i in appointments
        ]

        notes = [
            (i.when, "note",  i) for i in patient_consultations if i.when
        ]

        timeline = sorted(obs + notes + appointments, key=lambda x: x[0], reverse=True)

        return {
            "episode": episode,
            "demographics": demographics,
            "timeline": timeline,
        }

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        patients = self.get_patients()
        ctx["rows"] = self.patients_to_rows(patients)
        return ctx


class OutstandingActionsMDT(LoginRequiredMixin, TemplateView):
    template_name = "tb/mdt_list_outstanding.html"

    def get_patient_consultations(self):
        mdt_meeting = PatientConsultationReasonForInteraction.objects.get(
            name="MDT meeting"
        )
        return PatientConsultation.objects.exclude(
            plan=""
        ).exclude(
            when=None
        ).filter(
            reason_for_interaction_fk_id=mdt_meeting.id
        )

    def get_patients(self):
        episode_ids = self.get_patient_consultations().values_list(
            'episode_id', flat=True
        )

        return Patient.objects.filter(
            episode__id__in=episode_ids
        ).prefetch_related(
            'demographics_set',
            'episode_set',
        )

    def patients_to_rows(self, patients):
        result = []
        consultations = self.get_patient_consultations().select_related(
            'episode'
        )
        patient_id_to_consultations = defaultdict(list)
        for pc in consultations:
            patient_id_to_consultations[pc.episode.patient_id].append(pc)

        patient_id_to_consultations = {
            patient_id: sorted(consultations, key=lambda x: x.when, reverse=True)
            for patient_id, consultations in patient_id_to_consultations.items()
        }

        patients = sorted(
            patients,
            key=lambda p: patient_id_to_consultations[p.id][0].when,
            reverse=True
        )

        for patient in patients:
            result.append(
                self.patient_to_row(patient, patient_id_to_consultations[patient.id])
            )

        return result

    def patient_to_row(self, patient, patient_consultations):
        demographics = patient.demographics_set.all()[0]

        tb_category = episode_categories.TbEpisode.display_name
        tb_episodes = [i for i in patient.episode_set.all() if i.category_name == tb_category]
        if tb_episodes:
            episode = tb_episodes[0]

        tb_episodes = [i for i in patient.episode_set.all() if i.category_name == tb_category]
        if tb_episodes:
            episode = tb_episodes[0]

        return {
            "episode": episode,
            "demographics": demographics,
            "mdt_notes": patient_consultations,
        }

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        patients = self.get_patients()
        ctx["rows"] = self.patients_to_rows(patients)
        return ctx

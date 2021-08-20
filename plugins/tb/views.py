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
from plugins.tb import episode_categories, constants, models, lab
from plugins.tb.models import (
    AFBRefLab,
    PatientConsultation,
    AFBCulture,
    Treatment,
    TBPCR,
)
from plugins.labtests import models as lab_models
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
        last_qf_obs = (
            lab_models.Observation.objects.filter(
                test__patient=patient,
                test__test_name="QUANTIFERON TB GOLD IT",
                observation_name="QFT TB interpretation",
            )
            .exclude(observation_value__iexact="pending")
            .order_by("-observation_datetime")
            .first()
        )
        ctx["igra"] = []
        if last_qf_obs:
            last_qf_test = last_qf_obs.test
            ctx["igra"] = [
                last_qf_test.observation_set.filter(
                    observation_name="QFT TB interpretation"
                ).first(),
                last_qf_test.observation_set.filter(
                    observation_name="QFT IFN gamma result (TB1)"
                ).first(),
                last_qf_test.observation_set.filter(
                    observation_name="QFT IFN gamma result (TB2)"
                ).first(),
            ]
            ctx["igra"] = [i for i in ctx["igra"] if i]

        # Show the last positive culture and PCR and the last recent resulted if later
        # than the last positive
        pcr_qs = TBPCR.objects.filter(patient=self.object.episode.patient)
        last_positive_pcr = (
            pcr_qs.filter(positive=True)
            .filter(patient=self.object.episode.patient)
            .order_by("-observation_datetime")
            .first()
        )
        if last_positive_pcr:
            last_resulted = (
                pcr_qs.filter(pending=False)
                .filter(
                    observation_datetime__date__gt=last_positive_pcr.observation_datetime.date()
                )
                .order_by("-observation_datetime")
                .first()
            )
        else:
            last_resulted = (
                pcr_qs.filter(pending=False).order_by("-observation_datetime").first()
            )
        ctx["pcrs"] = [i for i in [last_positive_pcr, last_resulted] if i]
        ctx["pcrs"].reverse()

        afb_qs = AFBRefLab.objects.filter(patient=self.object.episode.patient)
        last_positive_culture = (
            afb_qs.filter(positive=True).order_by("-observation_datetime").first()
        )
        if last_positive_culture:
            last_resulted = (
                afb_qs.filter(pending=False)
                .filter(
                    observation_datetime__date__gt=last_positive_culture.observation_datetime.date()
                )
                .order_by("-observation_datetime")
                .first()
            )
        else:
            last_resulted = (
                afb_qs.filter(pending=False).order_by("-observation_datetime").first()
            )
        ctx["cultures"] = [i for i in [last_positive_culture, last_resulted] if i]
        ctx["cultures"].reverse()

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

    def get_lab_test_observations(
        self, patient, clinical_advice, test_name, observation_names
    ):
        """
        Return a lab test where at least one of the observations for
        that day are numeric
        """
        if not clinical_advice.when:
            return []
        last_lab_tests = (
            patient.lab_tests.filter(test_name=test_name)
            .filter(datetime_ordered__lt=clinical_advice.when)
            .prefetch_related("observation_set")
            .order_by("-datetime_ordered")
            .reverse()
        )
        test = None
        for last_lab_test in last_lab_tests:
            for observation in last_lab_test.observation_set.all():
                if observation.observation_name in observation_names:
                    test = last_lab_test
                    break
        if not test:
            return []
        observations = last_lab_test.observation_set.all()
        return [i for i in observations if i.observation_name in observation_names]

    def get_bloods(self, patient, clinical_advice):
        """
        Returns the most recent observations before the clincial
        advice for liver, urea, CRP, and full blood count observations.
        """
        result = []

        # Liver observations
        result.extend(
            self.get_lab_test_observations(
                patient,
                clinical_advice,
                "LIVER PROFILE",
                ["ALT", "AST", "Albumin", "Alkaline Phosphatase", "Total Bilirubin"],
            )
        )

        # Urea observations
        result.extend(
            self.get_lab_test_observations(
                patient,
                clinical_advice,
                "UREA AND ELECTROLYTES",
                ["Creatinine", "Potassium", "Sodium", "Urea"],
            )
        )

        # CRP
        result.extend(
            self.get_lab_test_observations(
                patient, clinical_advice, "C REACTIVE PROTEIN", ["C Reactive Protein"]
            )
        )

        # Full blood count
        result.extend(
            self.get_lab_test_observations(
                patient,
                clinical_advice,
                "C FULL BLOOD COUNT",
                ["Hb", "WBC", "Platelets"],
            )
        )
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
                result[obs_field] = str(obs_val).rsplit(".0", 1)[0]
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
            ctx["bloods_normal"] = not any(
                [i for i in ctx["bloods"] if i.is_outside_reference_range()]
            )
        ctx["diagnosis"] = episode.diagnosis_set.filter(
            category=Diagnosis.PRIMARY
        ).first()
        tb_treatments = episode.treatment_set.filter(category=Treatment.TB)
        tb_treatments = sorted(
            [i for i in tb_treatments if i.start_date], key=lambda x: x.start_date
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
        ctx["rows_by_date"] = defaultdict(lambda: defaultdict(list))
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
            start_date = admission.start_datetime.date()
            if admission.status_code == "Canceled":
                ctx["rows_by_date"][start_date]["canceled"].append(
                    (
                        admission,
                        demographics,
                        tb_episode,
                        recent_consultation,
                    )
                )
            else:
                ctx["rows_by_date"][start_date]["not_canceled"].append(
                    (
                        admission,
                        demographics,
                        tb_episode,
                        recent_consultation,
                    )
                )

        # defualteddict doesn't let you use items in a template
        # so lets just cast it to regular old dicts
        ctx["rows_by_date"] = {k: dict(v) for k, v in ctx["rows_by_date"].items()}

        for some_date, state_dict in ctx["rows_by_date"].items():
            not_canceled = state_dict["not_canceled"]
            recent_consultation = [
                k[3] for k in not_canceled if k[3] and k[3].when.date() == some_date
            ]
            ctx["rows_by_date"][some_date]["stats"] = {
                "on_elcid": len(recent_consultation)
            }
        return ctx


class ClinicListForDate(AbstractTBAppointmentList):
    template_name = "tb/tb_patient_list.html"

    @property
    def name(self):
        return f"Clinic list for {self.date_stamp.strftime('%-d %b %Y')}"

    @property
    def date_stamp(self):
        date_stamp = self.kwargs["date_stamp"]
        return datetime.datetime.strptime(date_stamp, "%d%b%Y").date()

    def get_queryset(self, *args, **kwargs):
        appointment_types = constants.TB_APPOINTMENT_CODES
        return (
            Appointment.objects.filter(derived_appointment_type__in=appointment_types)
            .filter(
                start_datetime__date=self.date_stamp,
            )
            .prefetch_related("patient__episode_set")
        )


class ClinicList(AbstractTBAppointmentList):
    template_name = "tb/tb_patient_list.html"
    name = "TB Clinic List"

    def get_queryset(self, *args, **kwargs):
        today = timezone.now().date()
        until = today + datetime.timedelta(30)
        appointment_types = constants.RFH_TB_APPOINTMENT_CODES
        return (
            Appointment.objects.filter(derived_appointment_type__in=appointment_types)
            .filter(start_datetime__date__gte=today, start_datetime__date__lte=until)
            .order_by("start_datetime")
            .prefetch_related("patient__episode_set")
        )


class Last30Days(AbstractTBAppointmentList):
    template_name = "tb/tb_patient_list.html"
    name = "Clinic History: last 30 days"

    def get_queryset(self, *args, **kwargs):
        today = timezone.now().date()
        until = today - datetime.timedelta(30)
        appointment_types = constants.RFH_TB_APPOINTMENT_CODES
        appointments = (
            Appointment.objects.filter(derived_appointment_type__in=appointment_types)
            .filter(start_datetime__lte=today, start_datetime__gte=until)
            .exclude(status_code="Canceled")
            .order_by("start_datetime")
            .prefetch_related("patient__episode_set")
        )
        return sorted(appointments, key=lambda x: x.start_datetime.date(), reverse=True)


class PrintConsultation(LoginRequiredMixin, DetailView):
    model = models.PatientConsultation
    template_name = "tb/patient_consultation_print.html"


class MDTList(LoginRequiredMixin, TemplateView):
    template_name = "tb/mdt_list.html"
    BARNET = "barnet"
    RFH = "rfh"
    SITES = [RFH, BARNET]
    ALL_OBS = [
        models.TBPCR,
        models.AFBSmear,
        models.AFBCulture,
        models.AFBRefLab,
    ]

    def patients_to_rows(self, patients):
        filter_kwargs = {
            "patient__in": patients,
            "reported_datetime__isnull": False,
            "positive": True,
        }

        patient_id_to_obs = defaultdict(list)
        for obs_model in self.ALL_OBS:
            qs = obs_model.objects.filter(**filter_kwargs)
            for obs in qs:
                patient_id_to_obs[obs.patient_id].append(obs)

        patient_id_to_obs = {
            patient_id: sorted(obs, key=lambda x: x.reported_datetime, reverse=True)
            for patient_id, obs in patient_id_to_obs.items()
        }

        patient_consultations = models.PatientConsultation.objects.filter(
            episode__patient__in=patients
        ).select_related("episode")
        patient_id_to_consultations = defaultdict(list)
        for pc in patient_consultations:
            patient_id_to_consultations[pc.episode.patient_id].append(pc)

        # Make sure the list is sorted by the most recent observation
        patients = sorted(
            patients,
            key=lambda x: patient_id_to_obs[x.id][0].reported_datetime,
            reverse=True,
        )

        result = []
        for patient in patients:
            result.append(
                self.patient_to_row(
                    patient,
                    patient_id_to_obs[patient.id],
                    patient_id_to_consultations[patient.id],
                )
            )
        return result

    @property
    def end_date(self):
        today = datetime.date.today()
        for i in range(7):
            some_date = today + datetime.timedelta(i)
            if some_date.isoweekday() == 3:
                return some_date

    @property
    def start_date(self):
        return self.end_date - datetime.timedelta(7)

    def title(self):
        from_dt = self.start_date.strftime("%-d %b %Y")
        title = f"Patients with positive, pcrs, cultures and ref lab reports reported after {from_dt}"
        return title.replace("  ", " ")

    def get_patients(self):
        filter_args = {"reported_datetime__gte": self.start_date, "positive": True}
        if self.kwargs["site"] == self.BARNET:
            filter_args["lab_number__contains"] = "K"
        else:
            filter_args["lab_number__contains"] = "L"
        patient_ids = set()
        for tb_obs_model in self.ALL_OBS:
            patient_ids = patient_ids.union(
                tb_obs_model.objects.filter(**filter_args).values_list(
                    "patient_id", flat=True
                )
            )
        return (
            Patient.objects.filter(id__in=patient_ids)
            .prefetch_related("demographics_set", "episode_set", "appointments")
            .distinct()
        )

    def filter_obs(self, obs):
        # The smear, culture and ref lab are all derrived from the same test
        # and all have the same reported date.
        # We only care about the culture if the ref lab is pending.
        # We only care about the smear if the culture is pending.
        #
        # So we only show the most important result for a day that we
        # can find.
        #
        #
        # Multiple tests are often done on the same day, if they
        # have the same value just show the first value

        date_to_obs = defaultdict(list)
        date_to_filtered_obs = {}

        for ob in obs:
            date_to_obs[ob.reported_datetime.date()].append(ob)

        # If there is a ref lab, filter out culture and smear
        # Else if there is a culture, filter out smears
        for some_date, obs in date_to_obs.items():
            if any([i for i in obs if isinstance(i, models.AFBRefLab)]):
                obs = [
                    i
                    for i in obs
                    if not isinstance(
                        i,
                        (
                            models.AFBSmear,
                            models.AFBCulture,
                        ),
                    )
                ]
            elif any([i for i in obs if isinstance(i, models.AFBCulture)]):
                obs = [i for i in obs if not isinstance(i, models.AFBSmear)]
            date_to_filtered_obs[some_date] = obs

        # create a dictionary of date to a unique list of observation values
        date_to_values = {}
        for some_date, obs in date_to_filtered_obs.items():
            date_to_values[some_date] = set([i.value for i in obs])

        date_to_unique_obs = defaultdict(list)
        for some_date, values in date_to_values.items():
            for value in list(values):
                date_to_unique_obs[some_date].append(
                    [i for i in date_to_filtered_obs[some_date] if i.value == value][0]
                )
        result = []
        for obs in date_to_unique_obs.values():
            result.extend(obs)
        return result

    def patient_to_row(self, patient, obs, patient_consultations):
        demographics = patient.demographics_set.all()[0]
        tb_category = episode_categories.TbEpisode.display_name
        tb_episodes = [
            i for i in patient.episode_set.all() if i.category_name == tb_category
        ]
        episode = None
        if tb_episodes:
            episode = tb_episodes[0]

        obs = [(i.reported_datetime, "obs", i) for i in self.filter_obs(obs)]

        # Only show the first TB related appointment and all
        # future TB related appointments
        appointments = []
        for appointment in patient.appointments.all():
            appt_type = appointment.derived_appointment_type
            if appt_type in constants.TB_NEW_APPOINTMENT_CODES:
                appointments.append(appointment)
            elif appt_type in constants.TB_APPOINTMENT_CODES:
                if appointment.start_datetime > timezone.now():
                    appointments.append(appointment)

        appointments = [
            (
                i.start_datetime,
                "appointment",
                i,
            )
            for i in appointments
        ]

        notes = [(i.when, "note", i) for i in patient_consultations if i.when]

        timeline = obs + notes + appointments
        timeline = sorted(timeline, key=lambda x: x[0], reverse=True)

        return {
            "episode": episode,
            "demographics": demographics,
            "timeline": timeline,
        }

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        patients = self.get_patients()
        ctx["rows"] = self.patients_to_rows(patients)
        ctx["last_week"] = self.start_date
        return ctx


class OutstandingActionsMDT(LoginRequiredMixin, TemplateView):
    template_name = "tb/mdt_list_outstanding.html"

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        mdt_meeting = PatientConsultationReasonForInteraction.objects.get(
            name="MDT meeting"
        )
        patient_consultations = (
            PatientConsultation.objects.exclude(plan="")
            .exclude(when=None)
            .filter(reason_for_interaction_fk_id=mdt_meeting.id)
            .select_related("episode")
        )
        episodes = [i.episode for i in patient_consultations]
        demographics = Demographics.objects.filter(patient__episode__in=episodes)
        patient_id_to_demographics = {i.patient_id: i for i in demographics}
        date_to_episode_to_mdt_notes = defaultdict(lambda: defaultdict(list))
        for patient_consultation in patient_consultations:
            episode = patient_consultation.episode
            date_to_episode_to_mdt_notes[patient_consultation.when.date()][
                episode
            ].append(patient_consultation)

        date_to_rows = defaultdict(list)

        for date, episode_to_mdt_notes in date_to_episode_to_mdt_notes.items():
            for episode, mdt_notes in episode_to_mdt_notes.items():
                date_to_rows[date].append(
                    {
                        "episode": episode,
                        "mdt_notes": sorted(
                            mdt_notes, key=lambda x: x.when, reverse=True
                        ),
                        "demographics": patient_id_to_demographics[episode.patient_id],
                    }
                )

        # sort the date to rows by reverse date
        date_to_rows = {
            k: v
            for k, v in sorted(date_to_rows.items(), key=lambda x: x[0], reverse=True)
        }
        # sort the rows in date to rows by the latest mdt note
        for some_date in date_to_rows.keys():
            date_to_rows[some_date] = sorted(
                date_to_rows[some_date],
                key=lambda x: x["mdt_notes"][0].when,
                reverse=True,
            )

        ctx["date_to_rows"] = date_to_rows
        ctx["num_consultations"] = len(patient_consultations)
        return ctx


class ClinicActivity(LoginRequiredMixin, TemplateView):
    template_name = "tb/stats/clinic_activity.html"

    @property
    def start_date(self):
        return datetime.date(2020, 1, 1)

    @property
    def end_date(self):
        return datetime.date(2021, 1, 1)

    @property
    def periods(self):
        result = []
        for i in range(12):
            start_month = self.start_date.month + (i % 12)
            start_year = self.start_date.year + int(i / 12)
            end_month = self.start_date.month + ((i + 1) % 12)
            end_year = self.start_date.year + int((i + 1) / 12)
            result.append(
                (
                    datetime.date(start_year, start_month, 1),
                    datetime.date(end_year, end_month, 1),
                )
            )
        return result

    def summary(self):
        number_of_attended_appointments = (
            Appointment.objects.filter(
                derived_appointment_type__in=constants.RFH_TB_APPOINTMENT_CODES
            )
            .filter(start_datetime__date__gt=self.start_date)
            .filter(end_datetime__date__lt=self.end_date)
            .exclude(status_code__in=["Canceled", "No Show"])
            .count()
        )
        patient_ids = set(
            Appointment.objects.filter(
                derived_appointment_type__in=constants.RFH_TB_APPOINTMENT_CODES
            )
            .filter(start_datetime__date__gt=self.start_date)
            .filter(end_datetime__date__lt=self.end_date)
            .exclude(status_code__in=["Canceled", "No Show"])
            .values_list("patient_id", flat=True)
            .distinct()
        )
        number_of_patients = len(patient_ids)
        patients_with_future_appointments = set(
            Appointment.objects.filter(
                derived_appointment_type__in=constants.RFH_TB_APPOINTMENT_CODES
            )
            .filter(start_datetime__date__gt=self.end_date)
            .filter(patient_id__in=patient_ids)
            .values_list("patient_id", flat=True)
            .distinct()
        )
        number_of_patients_who_had_their_last_appointment = number_of_patients - len(
            patients_with_future_appointments
        )
        return {
            "number_of_appointments": number_of_attended_appointments,
            "number_of_patients": number_of_patients,
            "number_of_patients_who_had_their_last_appointment": number_of_patients_who_had_their_last_appointment,
        }

    def appointments_by_status(self, *args, **kwargs):
        appointments = (
            Appointment.objects.filter(
                derived_appointment_type__in=constants.RFH_TB_APPOINTMENT_CODES
            )
            .filter(start_datetime__date__gte=self.start_date)
            .filter(end_datetime__date__lt=self.end_date)
        )
        appointment_type_month_count = defaultdict(lambda: [0 for i in self.periods])

        for appointment in appointments:
            appointment_type_month_count[appointment.status_code][
                appointment.start_datetime.month-1
            ] += 1

        return {
            "x": [i[0].strftime("%b") for i in self.periods],
            "vals": [[k] + v for k, v in appointment_type_month_count.items()],
        }

    def appointments_by_type(self):
        appointments = (
            Appointment.objects.filter(
                derived_appointment_type__in=constants.RFH_TB_APPOINTMENT_CODES
            )
            .filter(start_datetime__date__gte=self.start_date)
            .filter(end_datetime__date__lt=self.end_date)
            .exclude(status_code__in=["Canceled", "No Show"])
        )
        type_to_count = defaultdict(int)
        for appointment in appointments:
            type_to_count[appointment.derived_appointment_type] += 1
        return {k: v for k, v in sorted(type_to_count.items(), key=lambda x: -x[1])}

    def patients_shared_with_other_clinics(self):
        patient_ids = (
            Appointment.objects.filter(
                derived_appointment_type__in=constants.RFH_TB_APPOINTMENT_CODES
            )
            .filter(start_datetime__date__gte=self.start_date)
            .filter(end_datetime__date__lt=self.end_date)
            .exclude(status_code__in=["Canceled", "No Show"])
        ).values_list(patient_id=True)
        other_appointments = (
            Appointment.objects.filter(
                derived_appointment_type__in=constants.RFH_TB_APPOINTMENT_CODES
            )
            .filter(start_datetime__date__gte=self.start_date)
            .filter(end_datetime__date__lt=self.end_date)
            .filter(patient_id__in=patient_ids)
            .exclude(derived_appointment_type__in=constants.RFH_TB_APPOINTMENT_CODES)
            .exclude(status_code__in=["Canceled", "No Show"])
        )
        result = defaultdict(set)
        for other_appointment in other_appointments:
            result[other_appointment.derived_appointment_type].add(
                other_appointment.patient_id
            )

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["summary"] = self.summary()
        ctx["appointments_by_status"] = self.appointments_by_status()
        ctx["appointments_by_type"] = self.appointments_by_type()
        return ctx


class TBActivity(LoginRequiredMixin, TemplateView):
    @property
    def start_date(self):
        return datetime.date(2020, 1, 1)

    @property
    def end_date(self):
        return datetime.date(2021, 6, 1)

    @property
    def periods(self):
        result = []
        for i in range(18):
            start_month = self.start_date.month + (i % 12)
            start_year = self.start_date.year + int(i / 12)
            end_month = self.start_date.month + ((i + 1) % 12)
            end_year = self.start_date.year + int((i + 1) / 12)
            result.append(
                (
                    datetime.date(start_year, start_month, 1),
                    datetime.date(end_year, end_month, 1),
                )
            )
        return result

    def get_positive_patient_ids_for_date_range(self, start_date, end_date):
        patient_ids = set()
        for obs in [lab.AFBSmear, lab.AFBCulture, lab.AFBRefLab, lab.TBPCR]:
            patient_ids = patient_ids.union(
                set(
                    obs.get_positive_observations()
                    .filter(observation_datetime__date__gte=start_date)
                    .filter(observation_datetime__date__lt=end_date)
                    .values_list("test__patient_id", flat=True)
                )
            )
        return patient_ids

    def get_new_positives_by_period(self):
        return {
            (datetime.date(2020, 1, 1), datetime.date(2020, 2, 1)): 14,
            (datetime.date(2020, 2, 1), datetime.date(2020, 3, 1)): 7,
            (datetime.date(2020, 3, 1), datetime.date(2020, 4, 1)): 10,
            (datetime.date(2020, 4, 1), datetime.date(2020, 5, 1)): 8,
            (datetime.date(2020, 5, 1), datetime.date(2020, 6, 1)): 10,
            (datetime.date(2020, 6, 1), datetime.date(2020, 7, 1)): 5,
            (datetime.date(2020, 7, 1), datetime.date(2020, 8, 1)): 11,
            (datetime.date(2020, 8, 1), datetime.date(2020, 9, 1)): 7,
            (datetime.date(2020, 9, 1), datetime.date(2020, 10, 1)): 11,
            (datetime.date(2020, 10, 1), datetime.date(2020, 11, 1)): 8,
            (datetime.date(2020, 11, 1), datetime.date(2020, 12, 1)): 10,
            (datetime.date(2020, 12, 1), datetime.date(2021, 1, 1)): 7,
            (datetime.date(2021, 1, 1), datetime.date(2021, 2, 1)): 7,
            (datetime.date(2021, 2, 1), datetime.date(2021, 3, 1)): 10,
            (datetime.date(2021, 3, 1), datetime.date(2021, 4, 1)): 16,
            (datetime.date(2021, 4, 1), datetime.date(2021, 5, 1)): 12,
            (datetime.date(2021, 5, 1), datetime.date(2021, 6, 1)): 18,
            (datetime.date(2021, 6, 1), datetime.date(2021, 7, 1)): 10,
        }
        previous_positives_patients = self.get_positive_patient_ids_for_date_range(
            datetime.date.min, self.start_date
        )
        result = {}
        for start_date, end_date in self.periods:
            pos_patients = self.get_positive_patient_ids_for_date_range(
                start_date, end_date
            )
            new_pos_patients = [
                i for i in list(pos_patients) if i not in previous_positives_patients
            ]
            result[(start_date, end_date)] = len(new_pos_patients)
            previous_positives_patients = previous_positives_patients.union(
                pos_patients
            )
        return result

    def get_patients_with_appointments_for_date_range(self, start_date, end_date):
        return list(
            Appointment.objects.filter(
                derived_appointment_type__in=constants.RFH_TB_APPOINTMENT_CODES
            )
            .filter(start_datetime__date__gt=start_date)
            .filter(end_datetime__date__lt=end_date)
            .exclude(status_code__in=["Canceled", "No Show"])
            .values_list("patient_id", flat=True)
        )

    def get_new_patients_appointments(self):
        return {
            (datetime.date(2020, 1, 1), datetime.date(2020, 2, 1)): 80,
            (datetime.date(2020, 2, 1), datetime.date(2020, 3, 1)): 155,
            (datetime.date(2020, 3, 1), datetime.date(2020, 4, 1)): 111,
            (datetime.date(2020, 4, 1), datetime.date(2020, 5, 1)): 41,
            (datetime.date(2020, 5, 1), datetime.date(2020, 6, 1)): 39,
            (datetime.date(2020, 6, 1), datetime.date(2020, 7, 1)): 74,
            (datetime.date(2020, 7, 1), datetime.date(2020, 8, 1)): 57,
            (datetime.date(2020, 8, 1), datetime.date(2020, 9, 1)): 42,
            (datetime.date(2020, 9, 1), datetime.date(2020, 10, 1)): 92,
            (datetime.date(2020, 10, 1), datetime.date(2020, 11, 1)): 76,
            (datetime.date(2020, 11, 1), datetime.date(2020, 12, 1)): 58,
            (datetime.date(2020, 12, 1), datetime.date(2021, 1, 1)): 55,
            (datetime.date(2021, 1, 1), datetime.date(2021, 2, 1)): 60,
            (datetime.date(2021, 2, 1), datetime.date(2021, 3, 1)): 43,
            (datetime.date(2021, 3, 1), datetime.date(2021, 4, 1)): 78,
            (datetime.date(2021, 4, 1), datetime.date(2021, 5, 1)): 75,
            (datetime.date(2021, 5, 1), datetime.date(2021, 6, 1)): 83,
            (datetime.date(2021, 6, 1), datetime.date(2021, 7, 1)): 88,
        }
        previous_patients = set(
            self.get_patients_with_appointments_for_date_range(
                datetime.date.min, self.start_date
            )
        )
        result = {}
        for start_date, end_date in self.periods:
            patients = self.get_patients_with_appointments_for_date_range(
                start_date, end_date
            )
            new_patients = [i for i in patients if i not in previous_patients]
            result[(start_date, end_date)] = len(new_patients)
            previous_patients = previous_patients.union(new_patients)
        return result

    def get_new_patients_with_appointments_for_date_range(self, start_date, end_date):
        return list(
            Appointment.objects.filter(
                derived_appointment_type__in=constants.RFH_TB_APPOINTMENT_CODES
            )
            .filter(start_datetime__date__gt=start_date)
            .filter(end_datetime__date__lt=end_date)
            .filter(derived_appointment_type__contains="New")
            .exclude(status_code__in=["Canceled", "No Show"])
            .values_list("patient_id", flat=True)
        )

    def get_new_appointments_with_new(self):
        return {
            (datetime.date(2020, 1, 1), datetime.date(2020, 2, 1)): 61,
            (datetime.date(2020, 2, 1), datetime.date(2020, 3, 1)): 72,
            (datetime.date(2020, 3, 1), datetime.date(2020, 4, 1)): 81,
            (datetime.date(2020, 4, 1), datetime.date(2020, 5, 1)): 30,
            (datetime.date(2020, 5, 1), datetime.date(2020, 6, 1)): 31,
            (datetime.date(2020, 6, 1), datetime.date(2020, 7, 1)): 40,
            (datetime.date(2020, 7, 1), datetime.date(2020, 8, 1)): 37,
            (datetime.date(2020, 8, 1), datetime.date(2020, 9, 1)): 32,
            (datetime.date(2020, 9, 1), datetime.date(2020, 10, 1)): 44,
            (datetime.date(2020, 10, 1), datetime.date(2020, 11, 1)): 53,
            (datetime.date(2020, 11, 1), datetime.date(2020, 12, 1)): 51,
            (datetime.date(2020, 12, 1), datetime.date(2021, 1, 1)): 31,
            (datetime.date(2021, 1, 1), datetime.date(2021, 2, 1)): 49,
            (datetime.date(2021, 2, 1), datetime.date(2021, 3, 1)): 23,
            (datetime.date(2021, 3, 1), datetime.date(2021, 4, 1)): 44,
            (datetime.date(2021, 4, 1), datetime.date(2021, 5, 1)): 54,
            (datetime.date(2021, 5, 1), datetime.date(2021, 6, 1)): 67,
            (datetime.date(2021, 6, 1), datetime.date(2021, 7, 1)): 82,
        }
        previous_patients = set(
            self.get_new_patients_with_appointments_for_date_range(
                datetime.date.min, self.start_date
            )
        )
        result = {}
        for start_date, end_date in self.periods:
            patients = self.get_new_patients_with_appointments_for_date_range(
                start_date, end_date
            )
            new_patients = [i for i in patients if i not in previous_patients]
            result[(start_date, end_date)] = len(new_patients)
            previous_patients = previous_patients.union(new_patients)
        return result

    def get_count_of_appointments_for_new_patients(self):
        pass

    def get_length_of_care(self):
        pass

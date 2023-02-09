"""
Views for the TB Opal Plugin
"""
import csv
import json
import datetime
import io
import zipfile
from collections import defaultdict
from django.http.response import StreamingHttpResponse
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView
from django.utils.functional import cached_property
from django.db.models import Q
from opal.core.serialization import deserialize_datetime
from opal.core import subrecords
from opal.models import (
    PatientConsultationReasonForInteraction, Patient, Episode
)
from elcid.models import (
    Diagnosis,
    Demographics,
    SymptomComplex, ReferralRoute
)
from elcid.utils import timing
from plugins.appointments.models import Appointment
from plugins.tb import episode_categories, constants, models
from plugins.tb.models import (
    AFBRefLab,
    AdverseReaction,
    CommuninicationConsiderations,
    Nationality,
    PatientConsultation,
    SocialHistory,
    TBHistory,
    Travel,
    Treatment,
    TBPCR,
)
from plugins.labtests import models as lab_models
from plugins.tb.utils import get_tb_summary_information


class ClinicalAdvicePrintView(LoginRequiredMixin, DetailView):
    template_name = "tb/clinical_advice.html"
    model = PatientConsultation


class AbstractLetterView(LoginRequiredMixin, DetailView):
    @classmethod
    def get_letter_context(cls, patient_consultation):
        """
        This generates the contet for the letter, it also
        generates the context for the note sent to EPR
        """
        ctx = {"object": patient_consultation}
        episode = patient_consultation.episode
        patient = patient_consultation.episode.patient
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
        last_qf_obs = lab_models.Observation.objects.filter(
            test__patient=patient,
            test__test_name='QUANTIFERON TB GOLD IT',
            observation_name='QFT TB interpretation'
        ).exclude(
            observation_value__iexact='pending'
        ).order_by('-observation_datetime').first()
        ctx["igra"] = []
        if last_qf_obs:
            last_qf_test = last_qf_obs.test
            ctx["igra"] = [
                last_qf_test.observation_set.filter(
                    observation_name='QFT TB interpretation'
                ).first(),
                last_qf_test.observation_set.filter(
                    observation_name='QFT IFN gamma result (TB1)'
                ).first(),
                last_qf_test.observation_set.filter(
                    observation_name='QFT IFN gamma result (TB2)'
                ).first()
            ]
            ctx["igra"] = [i for i in ctx["igra"] if i]

        # Show the last positive culture and PCR and the last recent resulted if later
        # than the last positive
        pcr_qs = TBPCR.objects.filter(patient=patient_consultation.episode.patient)
        last_positive_pcr = pcr_qs.filter(
            positive=True
        ).filter(
            patient=patient_consultation.episode.patient
        ).order_by(
            '-observation_datetime'
        ).first()
        if last_positive_pcr:
            last_resulted = pcr_qs.filter(pending=False).filter(
                observation_datetime__date__gt=last_positive_pcr.observation_datetime.date()
            ).order_by(
                '-observation_datetime'
            ).first()
        else:
            last_resulted = pcr_qs.filter(pending=False).order_by(
                '-observation_datetime'
            ).first()
        ctx["pcrs"] = [i for i in [last_positive_pcr, last_resulted] if i]
        ctx["pcrs"].reverse()

        afb_qs = AFBRefLab.objects.filter(patient=patient_consultation.episode.patient)
        last_positive_culture = afb_qs.filter(positive=True).order_by(
            '-observation_datetime'
        ).first()
        if last_positive_culture:
            last_resulted = afb_qs.filter(pending=False).filter(
                observation_datetime__date__gt=last_positive_culture.observation_datetime.date()
            ).order_by(
                '-observation_datetime'
            ).first()
        else:
            last_resulted = afb_qs.filter(pending=False).order_by(
                '-observation_datetime'
            ).first()
        ctx["cultures"] = [i for i in [last_positive_culture, last_resulted] if i]
        ctx["cultures"].reverse()

        ctx["travel_list"] = episode.travel_set.all()
        ctx["adverse_reaction_list"] = episode.adversereaction_set.all()
        ctx["past_medication_list"] = episode.antimicrobial_set.all()
        ctx["allergies_list"] = [i for i in patient.allergies_set.all() if i.drug or i.details]
        ctx["imaging_list"] = episode.imaging_set.all()
        ctx["tb_history"] = patient.tbhistory_set.get()
        ctx["index_case_list"] = patient.indexcase_set.all()
        ctx["other_investigation_list"] = episode.otherinvestigation_set.all()
        consultation_datetime = patient_consultation.when
        if consultation_datetime:
            obs = episode.observation_set.filter(
                datetime__date=consultation_datetime.date()
            ).last()
            if obs:
                ctx["weight"] = obs.weight
        return ctx

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.__class__.get_letter_context(self.object))
        return ctx


class InitialAssessment(AbstractLetterView):
    template_name = "tb/letters/initial_assessment.html"
    model = PatientConsultation

    @classmethod
    def get_letter_context(cls, patient_consultation):
        ctx = super().get_letter_context(patient_consultation)
        episode = patient_consultation.episode
        patient = patient_consultation.episode.patient
        ctx["referral"] = episode.referralroute_set.get()
        ctx["social_history"] = episode.socialhistory_set.get()

        ctx["symptom_complex_list"] = [i for i in episode.symptomcomplex_set.all() if i.symptoms.exists()]
        ctx["patient"] = patient
        return ctx


class FollowUp(AbstractLetterView):
    template_name = "tb/letters/follow_up.html"
    model = PatientConsultation


class NurseLetter(LoginRequiredMixin, DetailView):
    template_name = "tb/letters/nurse_letter.html"
    model = PatientConsultation

    @classmethod
    def get_lab_test_observations(cls, patient, clinical_advice, test_name, observation_names):
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

    @classmethod
    def get_bloods(cls, patient, clinical_advice):
        """
        Returns the most recent observations before the clincial
        advice for liver, urea, CRP, and full blood count observations.
        """
        result = []

        # Liver observations
        result.extend(cls.get_lab_test_observations(
            patient,
            clinical_advice,
            "LIVER PROFILE",
            ["ALT", "AST", "Albumin", "Alkaline Phosphatase", "Total Bilirubin"]
        ))

        # Urea observations
        result.extend(cls.get_lab_test_observations(
            patient,
            clinical_advice,
            "UREA AND ELECTROLYTES",
            ["Creatinine", "Potassium", "Sodium", "Urea"]
        ))

        # CRP
        result.extend(cls.get_lab_test_observations(
            patient,
            clinical_advice,
            "C REACTIVE PROTEIN",
            ["C Reactive Protein"]
        ))

        # Full blood count
        result.extend(cls.get_lab_test_observations(
            patient,
            clinical_advice,
            "C FULL BLOOD COUNT",
            ["Hb", "WBC", "Platelets"]
        ))
        return result

    @classmethod
    def get_observations(cls, patient_consultation):
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

    @classmethod
    def get_letter_context(cls, patient_consultation):
        """
        We declare the get context method in a class method
        so that we can also use the same context to
        create the letter that goes up to EPR
        """
        episode = patient_consultation.episode
        ctx = {"object": patient_consultation}
        ctx["patient"] = episode.patient
        ctx["bloods"] = cls.get_bloods(episode.patient, patient_consultation)
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
        ctx["observations"] = cls.get_observations(patient_consultation)
        return ctx

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx.update(self.__class__.get_letter_context(self.object))
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
            if admission.status_code == 'Canceled':
                ctx["rows_by_date"][start_date]['canceled'].append(
                    (
                        admission,
                        demographics,
                        tb_episode,
                        recent_consultation,
                    )
                )
            else:
                ctx["rows_by_date"][start_date]['not_canceled'].append(
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
            not_canceled = state_dict.get("not_canceled", [])
            recent_consultation = [
                k[3] for k in not_canceled if k[3] and k[3].when.date() == some_date
            ]
            ctx["rows_by_date"][some_date]["stats"] = {
                'on_elcid': len(recent_consultation)
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
        return Appointment.objects.filter(
            derived_appointment_type__in=appointment_types
        ).filter(
            start_datetime__date=self.date_stamp,
        ).prefetch_related(
            'patient__episode_set'
        )


class ClinicList(AbstractTBAppointmentList):
    template_name = "tb/tb_patient_list.html"
    name = "TB Clinic List"

    def get_queryset(self, *args, **kwargs):
        today = timezone.now().date()
        until = today + datetime.timedelta(30)
        appointment_types = constants.RFH_TB_APPOINTMENT_CODES
        return Appointment.objects.filter(
            derived_appointment_type__in=appointment_types
        ).filter(
            start_datetime__date__gte=today,
            start_datetime__date__lte=until
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
        appointment_types = constants.RFH_TB_APPOINTMENT_CODES
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
        return sorted(
            appointments, key=lambda x: x.start_datetime.date(), reverse=True
        )


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
            'patient__in': patients,
            'reported_datetime__isnull': False,
            'positive': True
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
        ).select_related('episode')
        patient_id_to_consultations = defaultdict(list)
        for pc in patient_consultations:
            patient_id_to_consultations[pc.episode.patient_id].append(pc)

        # Make sure the list is sorted by the most recent observation
        patients = sorted(
            patients,
            key=lambda x: patient_id_to_obs[x.id][0].reported_datetime,
            reverse=True
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
        filter_args = {
            "reported_datetime__gte": self.start_date,
            "positive": True
        }
        if self.kwargs["site"] == self.BARNET:
            filter_args["lab_number__contains"] = "K"
        else:
            filter_args["lab_number__contains"] = "L"
        patient_ids = set()
        for tb_obs_model in self.ALL_OBS:
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
                    i for i in obs if not isinstance(i, (
                        models.AFBSmear, models.AFBCulture,
                    ))
                ]
            elif any([i for i in obs if isinstance(i, models.AFBCulture)]):
                obs = [
                    i for i in obs if not isinstance(i, models.AFBSmear)
                ]
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
        tb_episodes = [i for i in patient.episode_set.all() if i.category_name == tb_category]
        episode = None
        if tb_episodes:
            episode = tb_episodes[0]

        obs = [
            (i.reported_datetime, 'obs', i) for i in self.filter_obs(obs)
        ]

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
            (i.start_datetime, "appointment", i,) for i in appointments
        ]

        notes = [
            (i.when, "note",  i) for i in patient_consultations if i.when
        ]

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


class OnTBMeds(LoginRequiredMixin, TemplateView):
    template_name = "tb/on_tb_meds.html"

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        today = datetime.date.today()
        treatments = Treatment.objects.filter(category=Treatment.TB).exclude(
            end_date__lte=today
        ).exclude(
            planned_end_date__lte=today
        ).order_by('-start_date').prefetch_related(
            'episode__patient__demographics_set'
        )

        demographics_to_treatments = defaultdict(list)

        for treatment in treatments:
            demographics = treatment.episode.patient.demographics_set.all()[0]
            demographics_to_treatments[demographics].append(treatment)
        ctx["demographics_and_treatments"] = sorted(
            demographics_to_treatments.items(), key=lambda x: x[0].surname.strip().lower()
        )
        return ctx


class OutstandingActionsMDT(LoginRequiredMixin, TemplateView):
    template_name = "tb/mdt_list_outstanding.html"

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        mdt_meeting = PatientConsultationReasonForInteraction.objects.get(
            name="MDT meeting"
        )
        patient_consultations = PatientConsultation.objects.exclude(
            plan=""
        ).exclude(
            when=None
        ).filter(
            reason_for_interaction_fk_id=mdt_meeting.id
        ).select_related('episode')
        episodes = [i.episode for i in patient_consultations]
        demographics = Demographics.objects.filter(
            patient__episode__in=episodes
        )
        patient_id_to_demographics = {
            i.patient_id: i for i in demographics
        }
        date_to_episode_to_mdt_notes = defaultdict(lambda: defaultdict(list))
        for patient_consultation in patient_consultations:
            episode = patient_consultation.episode
            date_to_episode_to_mdt_notes[patient_consultation.when.date()][episode].append(
                patient_consultation
            )

        date_to_rows = defaultdict(list)

        for date, episode_to_mdt_notes in date_to_episode_to_mdt_notes.items():
            for episode, mdt_notes in episode_to_mdt_notes.items():
                date_to_rows[date].append({
                    "episode": episode,
                    "mdt_notes": sorted(mdt_notes, key=lambda x: x.when, reverse=True),
                    "demographics": patient_id_to_demographics[episode.patient_id]
                })

        # sort the date to rows by reverse date
        date_to_rows = {
            k: v for k, v in sorted(
                date_to_rows.items(), key=lambda x: x[0], reverse=True
            )
        }
        # sort the rows in date to rows by the latest mdt note
        for some_date in date_to_rows.keys():
            date_to_rows[some_date] = sorted(
                date_to_rows[some_date],
                key=lambda x: x["mdt_notes"][0].when,
                reverse=True
            )

        ctx["date_to_rows"] = date_to_rows
        ctx["num_consultations"] = len(patient_consultations)
        return ctx


def zip_file_response(file_stem, csv_data):
    """
    Takes in a file_stem and a list of dicts
    returns an http response with a file called
    {file_stem}.zip, which unzips to {file_stem}.csv
    """
    csv_buffer = io.StringIO()
    wr = None
    if csv_data:
        headers = csv_data[0].keys()
        wr = csv.DictWriter(
            csv_buffer, fieldnames=headers
        )
        wr.writeheader()
        wr.writerows(csv_data)
    csv_buffer.seek(0)

    temp = io.BytesIO()
    with zipfile.ZipFile(temp, 'w') as archive:
        archive.writestr(f'{file_stem}.csv', csv_buffer.getvalue())

    response = StreamingHttpResponse(temp, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{file_stem}.zip"'
    response['Content-Length'] = temp.tell()

    temp.seek(0)

    return response


class AbstractClinicActivity(LoginRequiredMixin, TemplateView):
    @property
    def menu_years(self):
        minimum_year = 2019
        current_year = datetime.date.today().year
        result = []
        for i in range(4):
            start_year = current_year - i
            end_year = current_year - i + 1
            if start_year < minimum_year:
                break
            result.append((start_year, end_year,))
        result.reverse()
        return result

    @property
    def start_date(self):
        return datetime.date(int(self.kwargs["year"]), 1, 1)

    @property
    def end_date(self):
        return datetime.date(int(self.kwargs["year"]) + 1, 1, 1)

    @property
    def months(self):
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

    @property
    def weeks(self):
        result = []
        first_monday = None
        for i in range(7):
            first_monday = self.start_date - datetime.timedelta(i)
            if first_monday.isoweekday() == 1:
                break

        for i in range(52):
            if first_monday + datetime.timedelta(i * 7) < self.end_date:
                start = first_monday + datetime.timedelta(i * 7)
                end = first_monday + datetime.timedelta((i + 1) * 7)
                result.append((start, end))
            else:
                break
        return result

    @cached_property
    def appointments_qs(self):
        appointments = list(
            Appointment.objects.filter(
                derived_appointment_type__in=constants.RFH_TB_APPOINTMENT_CODES
            )
            .filter(start_datetime__date__gt=self.start_date)
            .filter(end_datetime__date__lt=self.end_date)
            .exclude(status_code__in=["Checked In", "Canceled"])
        )
        cleaned_appointments = []
        for appointment in appointments:
            if appointment.start_datetime < timezone.now():
                if appointment.status_code == 'Confirmed':
                    continue
            cleaned_appointments.append(appointment)
        return cleaned_appointments

    @cached_property
    def mdt_meeting_qs(self):
        mdt_meeting = PatientConsultationReasonForInteraction.objects.get(
            name="MDT meeting"
        )
        return list(
            PatientConsultation.objects.filter(
                when__date__gte=self.start_date,
                when__date__lt=self.end_date,
                reason_for_interaction_fk_id=mdt_meeting.id,
            ).select_related("episode")
        )

    @cached_property
    def non_mdt_consultations(self):
        mdt_meeting = PatientConsultationReasonForInteraction.objects.get(
            name="MDT meeting"
        )
        return list(
            PatientConsultation.objects.filter(when__date__gte=self.start_date)
            .filter(when__date__lt=self.end_date)
            .exclude(reason_for_interaction_fk_id=mdt_meeting.id)
            .select_related("episode")
        )

    @property
    def atttended_appointments(self):
        return [
            i
            for i in self.appointments_qs
            if i.status_code not in ["Canceled", "No Show"]
        ]


class ClinicActivity(AbstractClinicActivity):
    template_name = "tb/stats/clinic_activity.html"

    @timing
    def summary(self):
        attended_appointments = self.atttended_appointments
        number_of_attended_appointments = len(attended_appointments)
        patient_ids = set()
        for i in attended_appointments:
            patient_ids.add(i.patient_id)
        number_of_patients = len(patient_ids)
        number_of_new_patients = 0
        for i in attended_appointments:
            if i.derived_appointment_type in constants.TB_NEW_APPOINTMENT_CODES:
                number_of_new_patients += 1
        return {
            "number_of_appointments": number_of_attended_appointments,
            "number_of_patients": number_of_patients,
            "number_of_new_patients": number_of_new_patients,
        }

    @timing
    def appointments_by_status(self, *args, **kwargs):
        appointments = self.appointments_qs
        appointment_type_month_count = defaultdict(lambda: [0 for i in self.months])

        for appointment in appointments:
            appointment_type_month_count[appointment.status_code][
                appointment.start_datetime.month - 1
            ] += 1

        checked_out = appointment_type_month_count["Checked Out"]
        no_shows = appointment_type_month_count["No Show"]
        confirmed = appointment_type_month_count["Confirmed"]
        no_show_percentage = []
        today = datetime.date.today()
        for idx, month_checked_out in enumerate(checked_out):
            month_no_show = appointment_type_month_count["No Show"][idx]
            month_total = month_no_show + month_checked_out

            month = self.months[idx][0].month
            year = self.months[idx][0].year
            # only include the no show % for completed months
            if month_total and (month < today.month or year < today.year):
                no_show_percentage.append(int((month_no_show/month_total) * 100))
            else:
                no_show_percentage.append(None)
        months = [i[0].strftime("%b") for i in self.months]
        table_vals = [
            ["Attended"] + checked_out,
            ["No show"] + no_shows
        ]
        if any(confirmed):
            table_vals.append(["Confirmed"] + confirmed)
            table_vals = sorted(table_vals, key=lambda x: x[0])

        return {
            "x": json.dumps(months),
            "attendance_max": max(checked_out + [500]),
            "graph_vals": json.dumps([
                ["Attended"] + checked_out,
                ["No show (%)"] + no_show_percentage
            ]),
            "table_headers": months,
            "table_vals": table_vals
        }

    @timing
    def appointments_by_type(self):
        appointments = self.atttended_appointments
        type_to_count = defaultdict(int)
        for appointment in appointments:
            type_to_count[appointment.derived_appointment_type] += 1
        return {k: v for k, v in sorted(type_to_count.items(), key=lambda x: -x[1])}

    @timing
    def mdt_start_stop(self):
        pcs = self.mdt_meeting_qs
        by_week = defaultdict(list)
        for pc in pcs:
            for start_week, end_week in self.weeks:
                if pc.when.date() >= start_week:
                    if pc.when.date() < end_week:
                        by_week[start_week].append(pc)
        count = dict()
        for start, _ in self.weeks:
            pcs = by_week.get(start, [])
            if not pcs:
                count[start] = 0
            else:
                whens = [i.when for i in pcs]
                count[start] = len(whens)
        return {
            "x_axis": json.dumps(
                [f"{i.strftime('%d/%m')}-{b.strftime('%d/%m')}" for i, b in self.weeks]
            ),
            "vals": json.dumps(
                [
                    ["count"] + list(count.values()),
                ]
            ),
        }

    def elcid_review(self):
        # recorded on elcid by appointment type
        # patients on elcid
        pcs = self.non_mdt_consultations
        pcs_by_patient_id_date = {
            (i.episode.patient_id, i.when.date(),): i for i in pcs
        }
        appointments = self.atttended_appointments
        appt_types = list(set(i.derived_appointment_type for i in appointments))
        appt_types = sorted(appt_types)
        appt_types_to_values = defaultdict(list)
        table_rows = defaultdict(list)
        for start_date, end_date in self.months:
            months_appointments = []
            for appointment in appointments:
                app_start = appointment.start_datetime.date()
                if start_date <= app_start and end_date > app_start:
                    months_appointments.append(appointment)
            on_elcid_by_type = defaultdict(int)
            by_type = defaultdict(int)
            for appointment in months_appointments:
                appt_type = appointment.derived_appointment_type
                by_type[appt_type] += 1
                start = appointment.start_datetime
                key = (appointment.patient_id, start.date(),)
                # If there is an appointment on the day for the patient after the start
                # time then mark it as recorded on elcid
                pc = pcs_by_patient_id_date.get(key)
                if pc and start <= pc.when:
                    on_elcid_by_type[appt_type] += 1
                else:
                    # If there isn't a patient, see if there is a pc the
                    # next day and count that.
                    key = (appointment.patient_id, start.date() + datetime.timedelta(1),)
                    if key in pcs_by_patient_id_date:
                        on_elcid_by_type[appt_type] += 1
            for appt_type in appt_types:
                total = by_type[appt_type]
                on_elcid = on_elcid_by_type[appt_type]
                if total:
                    percent = int((on_elcid/total) * 100)
                else:
                    percent = 0
                appt_types_to_values[appt_type].append(percent)
                table_rows[appt_type].append((on_elcid, total, percent,))
        vals = []
        for appt_type in appt_types:
            values = appt_types_to_values[appt_type]
            if any(values):
                vals.append([f"{appt_type} recorded %"] + values)
        return {
            "x": [i[0].strftime("%b") for i in self.months],
            "vals": vals,
            "table": {
                "headers": [""] + [i[0].strftime("%b") for i in self.months],
                # exclude appointment types where nothing is populated on elcid
                "rows": {k: v for k, v in table_rows.items() if any(i[0] for i in v)}
            }
        }

    def users_recorded(self):
        """
        The users who recorded patient consultations in elcid
        """
        pcs = self.non_mdt_consultations
        by_initials = defaultdict(int)
        for pc in pcs:
            by_initials[pc.initials] += 1
        less_than_5 = 0
        result = dict()
        for k, v in by_initials.items():
            if v < 5:
                less_than_5 += v
            else:
                result[k] = v
        result = dict(sorted(
            result.items(), key=lambda x: x[1], reverse=True
        ))
        result["Other (<5)"] = less_than_5
        return result

    def patient_notes_by_reason_for_interaction(self):
        pcs = self.non_mdt_consultations + self.mdt_meeting_qs
        result = defaultdict(int)
        for pc in pcs:
            result[pc.reason_for_interaction] += 1
        result = dict(sorted(
            result.items(), key=lambda x: x[1], reverse=True
        ))
        return result

    def get_subrecord_with_appointment_count(self, subrecord, qs=None):
        """
        for patients with appointments this year, tell
        me if the subrecord has been fille din.
        """
        patient_ids = list(set([i.patient_id for i in self.appointments_qs]))
        if not qs:
            qs = subrecord.objects.all()
        if getattr(subrecord, "_is_singleton", False):
            qs = qs.exclude(
                consistency_token=''
            )
        if subrecord in set(subrecords.patient_subrecords()):
            qs = qs.filter(
                patient__episode__category_name=episode_categories.TbEpisode.display_name
            )
            return len(set(qs.filter(
                patient_id__in=patient_ids
            ).values_list(
                'patient_id', flat=True
            ).distinct()))
        else:
            qs = qs.filter(
                episode__category_name=episode_categories.TbEpisode.display_name
            )
            return len(set(qs.filter(
                episode__patient_id__in=patient_ids
            ).values_list(
                'episode_id', flat=True
            ).distinct()))

    def subrecords_recorded(self):
        patient_ids = list(set([
            i.episode.patient_id for i in self.non_mdt_consultations
        ]))
        result = {}
        result["Patient Notes"] = len(patient_ids)
        result["Primary Diagnosis"] = self.get_subrecord_with_appointment_count(
            Diagnosis, Diagnosis.objects.filter(
                category=Diagnosis.PRIMARY
            )
        )
        result["Seconday Diagnosis"] = self.get_subrecord_with_appointment_count(
            Diagnosis, Diagnosis.objects.exclude(
                category=Diagnosis.PRIMARY
            )
        )
        result[SymptomComplex.get_display_name()] = self.get_subrecord_with_appointment_count(
            SymptomComplex
        )
        result["TB Medication"] = self.get_subrecord_with_appointment_count(
            Treatment, Treatment.objects.filter(category=Treatment.TB)
        )
        result["Other Medication"] = self.get_subrecord_with_appointment_count(
            Treatment, Treatment.objects.exclude(category=Treatment.TB)
        )
        result[AdverseReaction.get_display_name()] = self.get_subrecord_with_appointment_count(
            AdverseReaction
        )
        result[ReferralRoute.get_display_name()] = self.get_subrecord_with_appointment_count(
            ReferralRoute
        )
        language = set(
            CommuninicationConsiderations.objects.filter(
                patient_id__in=patient_ids
            ).exclude(
                updated=None
            ).values_list('patient_id', flat=True).distinct()
        )
        nationality = set(
            Nationality.objects.filter(
                patient_id__in=patient_ids
            ).exclude(
                updated=None
            ).values_list('patient_id', flat=True).distinct()
        )
        nationality_and_language = language.union(nationality)
        result["Nationality and Language"] = len(nationality_and_language)
        result[Travel.get_display_name()] = self.get_subrecord_with_appointment_count(
            Travel
        )
        result[TBHistory.get_display_name()] = self.get_subrecord_with_appointment_count(
            TBHistory
        )
        result[SocialHistory.get_display_name()] = self.get_subrecord_with_appointment_count(
            SocialHistory
        )
        return result

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["summary"] = self.summary()
        ctx["appointments_by_status"] = self.appointments_by_status()
        ctx["appointments_by_type"] = self.appointments_by_type()
        ctx["mdt_start_stop"] = self.mdt_start_stop()
        ctx["elcid_review"] = self.elcid_review()
        ctx["users_recorded"] = self.users_recorded()
        ctx["patient_notes_by_reason_for_interaction"] = self.patient_notes_by_reason_for_interaction()
        ctx["populated"] = self.subrecords_recorded()
        return ctx


class ClinicActivityMDTData(AbstractClinicActivity):
    template_name = "tb/stats/clinic_activity_mdt_data.html"

    def get_week(self, some_date):
        weeks = self.weeks
        week = [
            (i, v,) for i, v in weeks if some_date >= i and some_date < v
        ]
        return week[0]

    def get_mdt_info(self):
        mdt_meetings = self.mdt_meeting_qs
        patient_ids = set([i.episode.patient_id for i in mdt_meetings])
        demographics = Demographics.objects.filter(
            patient_id__in=patient_ids
        )
        patient_id_to_demographics = {i.patient_id: i for i in demographics}
        result = []
        for mdt_meeting in mdt_meetings:
            episode_id = mdt_meeting.episode_id
            patient_id = mdt_meeting.episode.patient_id
            host = self.request.get_host()
            link = f"http://{host}/#/patient/{patient_id}/{episode_id}"
            demographics = patient_id_to_demographics[patient_id]
            row = {
                "Link": link,
                "Name": demographics.name,
                "MRN": demographics.hospital_number,
                "When": mdt_meeting.when,
                "By": mdt_meeting.initials
            }
            if self.request.method == "POST":
                row["Examination findings"] = mdt_meeting.examination_findings
                row["Discussion"] = mdt_meeting.discussion
                row["Plan"] = mdt_meeting.plan
            result.append(row)

        result = sorted(result, key=lambda x: x["When"])
        return result

    def post(self, *args, **kwargs):
        table_data = self.get_mdt_info()
        return zip_file_response(f"mdt_data_{self.kwargs['year']}", table_data)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mdt_info = self.get_mdt_info()
        rows_by_week = defaultdict(list)
        for mdt_row in mdt_info:
            rows_by_week[self.get_week(mdt_row["When"].date())].append(
                mdt_row
            )
        ctx["rows_by_week"] = dict(rows_by_week)
        return ctx


class ClinicActivityAppointmentData(AbstractClinicActivity):
    template_name = "tb/stats/clinic_activity_appointment_data.html"

    def get_patient_ids_with_subrecords(self, subrecord, qs=None):
        """
        Return the patient ids for subrecords with appointments
        during the start/end dates
        """

        patient_ids = list(set([i.patient_id for i in self.appointments_qs]))
        if qs is None:
            qs = subrecord.objects.all()
        if getattr(subrecord, "_is_singleton", False):
            qs = qs.exclude(
                consistency_token=''
            )
        if subrecord in set(subrecords.patient_subrecords()):
            qs = qs.filter(
                patient__episode__category_name=episode_categories.TbEpisode.display_name
            )
            return set(qs.filter(
                patient_id__in=patient_ids
            ).values_list(
                'patient_id', flat=True
            ).distinct())
        else:
            qs = qs.filter(
                episode__category_name=episode_categories.TbEpisode.display_name
            )
            return set(qs.filter(
                episode__patient_id__in=patient_ids
            ).values_list(
                'episode__patient_id', flat=True
            ).distinct())

    def get_appointment_info(self):
        appointments = self.appointments_qs
        non_mdt_consultations = self.non_mdt_consultations
        initials_by_date = {
            i.when.date(): i.initials for i in non_mdt_consultations
        }
        patient_ids = set([i.patient_id for i in appointments])
        episodes = Episode.objects.filter(
            category_name=episode_categories.TbEpisode.display_name
        ).filter(
            patient_id__in=patient_ids
        )
        patient_id_to_episode_id = {
            i.patient_id: i.id for i in episodes
        }

        demographics = Demographics.objects.filter(patient_id__in=patient_ids)
        patient_id_to_demographics = {
            i.patient_id: i for i in demographics
        }
        primary_diagnosis_qs = Diagnosis.objects.filter(
            category=Diagnosis.PRIMARY
        )
        primary_diagnosis_patient_ids = self.get_patient_ids_with_subrecords(
            Diagnosis, primary_diagnosis_qs
        )
        symptom_patient_ids = self.get_patient_ids_with_subrecords(
            SymptomComplex
        )
        referral_patient_ids = self.get_patient_ids_with_subrecords(
            ReferralRoute
        )

        if self.request.method == "POST":
            secondary_diagnosis_qs = Diagnosis.objects.filter(
                category=Diagnosis.PRIMARY
            )
            secondary_diagnosis_patient_ids = self.get_patient_ids_with_subrecords(
                Diagnosis, secondary_diagnosis_qs
            )
            tb_medication_qs = Treatment.objects.filter(
                category=Treatment.TB
            )
            tb_medication_patient_ids = self.get_patient_ids_with_subrecords(
                Treatment, tb_medication_qs
            )
            other_medication_qs = Treatment.objects.exclude(
                category=Treatment.TB
            )
            other_medication_patient_ids = self.get_patient_ids_with_subrecords(
                Treatment, other_medication_qs
            )
            nationality_patient_ids = self.get_patient_ids_with_subrecords(
                Nationality
            )
            language_patient_ids = self.get_patient_ids_with_subrecords(
                CommuninicationConsiderations
            )
            travel_patient_ids = self.get_patient_ids_with_subrecords(
                Travel
            )
            tb_history_patient_ids = self.get_patient_ids_with_subrecords(
                TBHistory
            )
            social_history_patient_ids = self.get_patient_ids_with_subrecords(
                SocialHistory
            )

        result = []
        host = self.request.get_host()
        for appointment in appointments:
            patient_id = appointment.patient_id
            demographics = patient_id_to_demographics.get(
                patient_id
            )
            seen_by = False
            start_dt = appointment.start_datetime.date()
            seen_by = initials_by_date.get(start_dt)
            episode_id = patient_id_to_episode_id.get(patient_id)

            if episode_id:
                link = f"http://{host}/#/patient/{patient_id}/{episode_id}"
            else:
                link = f"http://{host}/#/patient/{patient_id}"
            if not seen_by:
                next_day = start_dt + datetime.timedelta(1)
                if next_day in initials_by_date:
                    seen_by = initials_by_date.get(next_day)
            row = {
                "Link": link,
                "Name": demographics.name,
                "MRN": demographics.hospital_number,
                "Start": appointment.start_datetime,
                "Type": appointment.derived_appointment_type,
                "Status": appointment.status_code,
                "Seen by": seen_by,
                "Primary diagnosis": patient_id in primary_diagnosis_patient_ids,
                SymptomComplex.get_display_name(): patient_id in symptom_patient_ids,
                ReferralRoute.get_display_name(): patient_id in referral_patient_ids
            }

            if self.request.method == "POST":
                has_sec_diag = patient_id in secondary_diagnosis_patient_ids
                row["Secondary diagnosis"] = has_sec_diag
                row["TB Medication"] = patient_id in tb_medication_patient_ids
                row["Other Medication"] = patient_id in other_medication_patient_ids
                has_nationality = patient_id in nationality_patient_ids
                has_language = patient_id in language_patient_ids
                row["Nationality and Language"] = has_nationality or has_language
                row[Travel.get_display_name()] = patient_id in travel_patient_ids
                row[TBHistory.get_display_name()] = patient_id in tb_history_patient_ids
                row[SocialHistory.get_display_name()] = patient_id in social_history_patient_ids
            result.append(row)
        result = sorted(result, key=lambda x: x["Start"])
        return result

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        appointment_info = self.get_appointment_info()
        by_month = defaultdict(list)
        for appointment_row in appointment_info:
            by_month[appointment_row["Start"].strftime('%B')].append(appointment_row)
        ctx["appointment_info_by_month"] = dict(by_month)
        return ctx

    def post(self, *args, **kwargs):
        c = self.get_appointment_info()
        return zip_file_response(f"appointments_{self.kwargs['year']}", c)

"""
Views for the TB Opal Plugin
"""
import datetime
from collections import defaultdict
from django.db.models import Q
from django.http.response import HttpResponseBadRequest
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.functional import cached_property
from django.utils import timezone
from django.views.generic import TemplateView
from opal.core.serialization import deserialize_datetime
from opal.models import Episode, PatientConsultationReasonForInteraction
from elcid.models import Diagnosis, Demographics
from plugins.appointments.models import Appointment
from opal.models import Patient
from plugins.tb import episode_categories, constants, lab, models
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
        return Appointment.objects.filter(
            derived_appointment_type__in=appointment_types
        ).filter(
           start_datetime__lte=today,
           start_datetime__gte=until
        ).exclude(
           status_code="Canceled"
        ).order_by(
           "-start_datetime"
        ).prefetch_related(
            'patient__episode_set'
        )


class PrintConsultation(LoginRequiredMixin, DetailView):
    model = models.PatientConsultation
    template_name = "tb/patient_consultation_print.html"


class MDTListOld(LoginRequiredMixin, TemplateView):
    template_name = "tb/mdt_list_old.html"
    BARNET = "Barnet"
    RFH = "RFH"

    @cached_property
    def positive_observations(self):
        culture_obs = list(lab.AFBCulture.get_positive_observations().filter(
            reported_datetime__gte=datetime.date.today() - datetime.timedelta(365)
        ).select_related('test'))
        smear_obs = list(lab.AFBSmear.get_positive_observations().filter(
            reported_datetime__gte=datetime.date.today() - datetime.timedelta(30)
        ).select_related('test'))
        pcr_tests = list(lab.TBPCR.get_positive_observations().filter(
            reported_datetime__gte=datetime.date.today() - datetime.timedelta(30)
        ).select_related('test'))
        return culture_obs + smear_obs + pcr_tests

    def get_observations(self):
        positive_obs = self.positive_observations
        return positive_obs + list(
            lab.AFBCulture.get_negative_observations().filter(
                reported_datetime__gte=datetime.date.today() - datetime.timedelta(365)
            )
        )

    def get_positive_observation_ids(self):
        return set([i.id for i in self.positive_observations])

    def get_patient_id_to_demographics(self, observations):
        patient_ids = set([i.test.patient_id for i in observations])
        demographics = Demographics.objects.filter(
            patient_id__in=patient_ids)
        result = {}
        for demo in demographics:
            result[demo.patient_id] = demo
        return result

    def format_obs_value(self, observation):
        tb_test = lab.get_tb_test(observation)
        obs_value_display = tb_test.display_observation_value(observation)
        return f"{observation.observation_name}: {obs_value_display}"

    def get_patient_id_to_lab_dicts(self, observations, positive_obs_ids):
        """
        We group the lab tests so if its
        for the same patient, site, observation date, is_positive, obs name and
        obs value, show them on the same line
        """
        patient_ids_to_lab_test_dict = defaultdict(list)

        group_tests = defaultdict(list)

        def get_key(observation):
            lab_test = observation.test
            return (
                lab_test.patient_id,
                lab_test.cleaned_site,
                observation.reported_datetime.date(),
                observation.id in positive_obs_ids,
                self.format_obs_value(observation)
            )
        for observation in observations:
            group_tests[get_key(observation)].append(observation.test.lab_number)

        for key, lab_numbers in group_tests.items():
            patient_id, site, reported, is_positive, obs_value = key
            patient_ids_to_lab_test_dict[patient_id].append({
                "site": site,
                "lab_numbers": ", ".join(lab_numbers),
                "reported": reported,
                "is_positive": is_positive,
                "observation_value": obs_value,
            })
        result = {}
        for patient_id, lab_test_dicts in patient_ids_to_lab_test_dict.items():
            result[patient_id] = sorted(
                lab_test_dicts, key=lambda x: x["reported"], reverse=True
            )
        return result

    def get_patient_id_to_tb_episode(self, observations):
        patient_ids = set([i.test.patient_id for i in observations])
        episodes = Episode.objects.filter(
            patient_id__in=patient_ids
        ).filter(
            category_name=episode_categories.TbEpisode.display_name
        )
        result = {}
        for episode in episodes:
            result[episode.patient_id] = episode
        return result

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        observations = self.get_observations()
        patient_id_to_demographics = self.get_patient_id_to_demographics(observations)
        positive_obs_ids = self.get_positive_observation_ids()
        patient_id_to_lab_test_dicts = self.get_patient_id_to_lab_dicts(observations, positive_obs_ids)
        patient_id_to_episode = self.get_patient_id_to_tb_episode(observations)

        patient_id_lab_test_dicts = sorted(
            patient_id_to_lab_test_dicts.items(),
            key=lambda lab_test_dicts: lab_test_dicts[1][0]["reported"],
            reverse=True
        )
        rows = []
        for patient_id, lab_test_dicts in patient_id_lab_test_dicts:
            episode = patient_id_to_episode.get(patient_id)
            demographics = patient_id_to_demographics[patient_id]
            # exclude patients with no hospital numbers
            if demographics.hospital_number:
                rows.append((episode, demographics, lab_test_dicts,))
        rfh_rows = []
        barnet_rows = []
        for row in rows:
            barnet = False
            rfh = False
            for test_set in row[2]:
                for lab_number in test_set["lab_numbers"]:
                    if "K" in lab_number:
                        barnet = True
                    if "L" in lab_number:
                        rfh = True
            if barnet:
                barnet_rows.append(row)
            if rfh:
                rfh_rows.append(row)
        ctx["location_to_rows"] = {
            "RFH": rfh_rows,
            "Barnet": barnet_rows
        }
        return ctx


class MDTList(LoginRequiredMixin, TemplateView):
    template_name = "tb/mdt_list.html"
    BARNET = "BARNET"
    RFH = "RFH"
    SITES = [RFH, BARNET]
    POSITIVE = "POSITIVE"
    RESULTED = "RESULTED"
    STATUSES = [POSITIVE, RESULTED]
    ALL_TESTS = "ALL_TESTS"
    CULTURE = "CULTURE"
    SMEAR = "SMEAR"
    PCR = "PCR"
    REF_LAB = "REF_LAB"
    TESTS = [
        ALL_TESTS, CULTURE, SMEAR, PCR, REF_LAB
    ]

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

    def filter_observations(self, qs):
        """
        Filters the observations based on query params
        """
        if self.request.GET["site"].upper() == self.BARNET:
            filter_letter = "K"
        else:
            filter_letter = "L"
        qs = qs.filter(test__lab_number__contains=filter_letter)
        qs = qs.filter(reported_datetime__gte=self.start_date)
        qs = qs.filter(reported_datetime__lte=self.end_date)
        return qs.select_related('test')

    @cached_property
    def positive_observations(self):
        tests = self.request.GET.get("tests")
        if tests == self.CULTURE:
            return self.filter_observations(
                lab.AFBCulture.get_positive_observations()
            )
        elif tests == self.SMEAR:
            return self.filter_observations(
                lab.AFBSmear.get_positive_observations()
            )
        elif tests == self.PCR:
            return self.filter_observations(
                lab.TBPCR.get_positive_observations()
            )
        elif tests == self.REF_LAB:
            return self.filter_observations(
                lab.AFBRefLib.get_positive_observations()
            )
        culture_obs = list(self.filter_observations(
            lab.AFBCulture.get_positive_observations()
        ))
        smear_obs = list(self.filter_observations(
            lab.AFBSmear.get_positive_observations()
        ))
        pcr_tests = list(self.filter_observations(
            lab.TBPCR.get_positive_observations()
        ))
        ref_lab_tests = list(self.filter_observations(
            lab.TBPCR.get_positive_observations()
        ))
        return culture_obs + smear_obs + pcr_tests + ref_lab_tests

    @cached_property
    def negative_observations(self):
        tests = self.request.GET.get("tests")
        if tests == self.CULTURE:
            return self.filter_observations(
                lab.AFBCulture.get_negative_observations()
            )
        elif tests == self.SMEAR:
            return self.filter_observations(
                lab.AFBSmear.get_negative_observations()
            )
        elif tests == self.PCR:
            return self.filter_observations(
                lab.TBPCR.get_negative_observations()
            )
        culture_obs = list(self.filter_observations(
            lab.AFBCulture.get_negative_observations()
        ))
        smear_obs = list(self.filter_observations(
            lab.AFBSmear.get_negative_observations()
        ))
        pcr_tests = list(self.filter_observations(
            lab.TBPCR.get_negative_observations()
        ))
        return culture_obs + smear_obs + pcr_tests

    def get_observations(self):
        positive_obs = self.positive_observations
        if self.request.GET.get("status") == self.RESULTED:
            return positive_obs + self.negative_observations
        return positive_obs

    def get_positive_observation_ids(self):
        return set([i.id for i in self.positive_observations])

    def get_patient_id_to_demographics(self, observations):
        patient_ids = set([i.test.patient_id for i in observations])
        demographics = Demographics.objects.filter(
            patient_id__in=patient_ids)
        result = {}
        for demo in demographics:
            result[demo.patient_id] = demo
        return result

    def format_obs_value(self, observation):
        tb_test = lab.get_tb_test(observation)
        obs_value_display = tb_test.display_observation_value(observation)
        return f"{observation.observation_name}: {obs_value_display}"

    def get_patient_id_to_lab_dicts(self, observations, positive_obs_ids):
        """
        We group the lab tests so if its
        for the same patient, site, observation date, is_positive, obs name and
        obs value, show them on the same line
        """
        patient_ids_to_lab_test_dict = defaultdict(list)

        group_tests = defaultdict(list)

        def get_key(observation):
            lab_test = observation.test
            return (
                lab_test.patient_id,
                lab_test.site_code,
                observation.reported_datetime.date(),
                observation.id in positive_obs_ids,
                self.format_obs_value(observation)
            )
        for observation in observations:
            group_tests[get_key(observation)].append(observation.test.lab_number)

        for key, lab_numbers in group_tests.items():
            patient_id, site, reported, is_positive, obs_value = key
            patient_ids_to_lab_test_dict[patient_id].append({
                "site": site,
                "lab_numbers": ", ".join(lab_numbers),
                "reported": reported,
                "is_positive": is_positive,
                "observation_value": obs_value,
            })
        result = {}
        for patient_id, lab_test_dicts in patient_ids_to_lab_test_dict.items():
            result[patient_id] = sorted(
                lab_test_dicts, key=lambda x: x["reported"], reverse=True
            )
        return result

    def get_patient_id_to_tb_episode(self, observations):
        patient_ids = set([i.test.patient_id for i in observations])
        episodes = Episode.objects.filter(
            patient_id__in=patient_ids
        ).filter(
            category_name=episode_categories.TbEpisode.display_name
        )
        result = {}
        for episode in episodes:
            result[episode.patient_id] = episode
        return result

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        if self.request.GET["site"].upper() not in self.SITES:
            raise HttpResponseBadRequest(f"Unknown site {self.request.GET['site']}")
        if self.request.GET.get("status").upper() not in self.STATUSES:
            raise HttpResponseBadRequest(f"Unknown status {self.request.GET['status']}")
        if self.request.GET.get("tests").upper() not in self.TESTS:
            raise HttpResponseBadRequest(f"Unknown status {self.request.GET['tests']}")
        observations = self.get_observations()
        patient_id_to_demographics = self.get_patient_id_to_demographics(observations)
        positive_obs_ids = self.get_positive_observation_ids()
        patient_id_to_lab_test_dicts = self.get_patient_id_to_lab_dicts(observations, positive_obs_ids)
        patient_id_to_episode = self.get_patient_id_to_tb_episode(observations)

        patient_id_lab_test_dicts = sorted(
            patient_id_to_lab_test_dicts.items(),
            key=lambda lab_test_dicts: lab_test_dicts[1][0]["reported"],
            reverse=True
        )
        rows = []
        for patient_id, lab_test_dicts in patient_id_lab_test_dicts:
            episode = patient_id_to_episode.get(patient_id)
            demographics = patient_id_to_demographics[patient_id]
            # exclude patients with no hospital numbers
            if demographics.hospital_number:
                rows.append((episode, demographics, lab_test_dicts,))
        ctx["rows"] = rows
        if self.request.GET["site"] == "RFH":
            ctx["site"] = "RFH"
        else:
            ctx["site"] = "Barnet"
        return ctx


class AbstractMDTList(LoginRequiredMixin, TemplateView):
    """
    Implement
    get_patients and return a qs of patients
    patient_to_row and return a row to appear in the table
    sort_rows to then sort the rows
    """
    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        patients = self.get_patients().prefetch_related(
            'demographics_set',
            'pcr_set',
            'afbsmear_set',
            'afbculture_set',
            'afbreflib_set',
            'episode_set'
        )
        rows = [
            self.patient_to_row(patient) for patient in patients
        ]
        ctx["rows"] = self.sort_rows(rows)
        return ctx

    def get_patients(self):
        pass

    def sort_rows(self, rows):
        return rows

    def get_first(self, some_tests):
        if some_tests:
            return some_tests[0]

    def patient_to_row(self, patient):
        demographics = patient.demographics_set.all()[0]

        pcrs = sorted(
            [i for i in patient.pcr_set.all() if not i.pending],
            key=lambda x: x.significant_date
        )
        first_positive_pcr = self.get_first([i for i in pcrs if i.positive])
        pcrs.reverse()
        latest_pcr = self.get_first(pcrs)

        smears = sorted(
            [i for i in patient.afbsmear_set.all() if not i.pending],
            key=lambda x: x.significant_date
        )
        first_positive_smear = self.get_first([i for i in smears if i.positive])
        smears.reverse()
        latest_smear = self.get_first(smears)

        cultures = sorted(
            [i for i in patient.afbculture_set.all() if not i.pending],
            key=lambda x: x.significant_date
        )
        first_positive_culture = self.get_first([i for i in cultures if i.positive])
        cultures.reverse()
        latest_culture = self.get_first(cultures)

        ref_libs = sorted(
            [i for i in patient.afbreflib_set.all() if not i.pending],
            key=lambda x: x.significant_date
        )
        first_positive_ref_lib = self.get_first([i for i in ref_libs if i.positive])
        ref_libs.reverse()
        latest_ref_lib = self.get_first(ref_libs)

        all_sorted = sorted(
            pcrs+smears+cultures+ref_libs, key=lambda x: x.significant_date
        )
        significant_date = datetime.datetime.min.date()
        if all_sorted:
            significant_date = all_sorted[-1].significant_date
        tb_category = episode_categories.TbEpisode.display_name
        episode = self.get_first([
            i for i in patient.episode_set.all()
            if i.category_name == tb_category
        ])

        patient_consultations = []

        if episode:
            patient_consultations = episode.patientconsultation_set.all().order_by(
                "-when"
            )

        first_tests = [
            first_positive_pcr,
            first_positive_smear,
        ]

        first_tests = sorted(
            [i for i in first_tests if i], key=lambda x: x.significant_date
        )

        first_test = None
        if first_tests:
            first_test = first_tests[0]
            if first_positive_culture:
                if first_positive_culture.significant_date < first_test.significant_date:
                    first_test = None

        last_tests = [
            latest_pcr, latest_smear
        ]

        last_tests = sorted(
            [i for i in last_tests if i],
            key=lambda x: x.significant_date,
            reverse=True
        )
        last_test = None
        if last_tests:
            last_test = last_tests[0]
            if latest_culture:
                if latest_culture.significant_date > last_test.significant_date:
                    last_test = None
            if last_test and latest_ref_lib:
                if latest_ref_lib.significant_date > last_test.significant_date:
                    last_test = None

        if first_positive_culture and latest_culture:
            if first_positive_culture == latest_culture:
                first_positive_culture = None

        if first_positive_ref_lib and latest_ref_lib:
            if first_positive_ref_lib == latest_ref_lib:
                first_positive_ref_lib = None

        tests = [
            ("Most recent resulted", last_test),
            ("Most recent ref lab report", latest_ref_lib),
            ("Most recent culture", latest_culture),
            ("First ref lab report", first_positive_ref_lib),
            ("First pos culture", first_positive_culture),
            ("First positive", first_test),
        ]

        tests = sorted(
            [(i, v) for i, v in tests if v],
            key=lambda x: x[1].significant_date,
            reverse=True
        )

        return {
            "episode": episode,
            "patient_consultations": patient_consultations,
            "demographics": demographics,
            "tests": tests,
            "significant_date": significant_date
        }


class MDTListExperimental(AbstractMDTList):
    template_name = "tb/mdt_list_experimental.html"
    BARNET = "BARNET"
    RFH = "RFH"
    SITES = [RFH, BARNET]
    POSITIVE = "POSITIVE"
    RESULTED = "RESULTED"
    STATUSES = [POSITIVE, RESULTED]
    ALL_TESTS = "ALL_TESTS"
    CULTURE = "CULTURE"
    SMEAR = "SMEAR"
    PCR = "PCR"
    REF_LAB = "REF_LAB"
    PCR_MODEL = models.PCR
    AFB_SMEAR_MODEL = models.AFBSmear
    AFB_CULTURE = models.AFBCulture
    AFB_REF_LIB = models.AFBRefLib
    TESTS = {
        ALL_TESTS: [
            models.PCR,
            models.AFBSmear,
            models.AFBCulture,
            models.AFBRefLib,
        ],
        CULTURE: [models.AFBCulture],
        SMEAR: [models.AFBSmear],
        REF_LAB: [models.AFBRefLib],
        PCR: [models.PCR],
    }

    @property
    def end_date(self):
        today = datetime.date.today()
        for i in range(7):
            some_date = today + datetime.timedelta(i)
            if some_date.isoweekday() == 2:
                return some_date

    @property
    def start_date(self):
        return self.end_date - datetime.timedelta(211)

    def get_patients(self):
        filter_args = {
            "significant_datetime__gte": self.start_date,
            "pending": False
        }
        if self.request.GET.get("status") == self.POSITIVE:
            filter_args["positive"] = True
        if self.request.GET["site"].upper() == self.BARNET:
            filter_args["lab_number__contains"] = "K"
        else:
            filter_args["lab_number__contains"] = "L"
        tests = self.TESTS[self.request.GET.get("tests")]
        patient_ids = set()
        for test in tests:
            patient_ids = patient_ids.union(test.objects.filter(
                **filter_args
            ).values_list('patient_id', flat=True))
        return Patient.objects.filter(
            id__in=patient_ids
        ).distinct()

    def sort_rows(self, rows):
        return sorted(rows, key=lambda x: x["significant_datetime"], reverse=True)


class OutstandingActionsMDT(AbstractMDTList):
    template_name = "tb/mdt_list_outstanding.html"

    def get_patient_consultations(self):
        mdt_meeting = PatientConsultationReasonForInteraction.objects.get(
            name="MDT meeting"
        )
        return PatientConsultation.objects.exclude(
            plan=""
        ).filter(
            reason_for_interaction_fk_id=mdt_meeting.id
        ).filter(
            Q(actioned=None) | Q(actioned=datetime.date.today())
        )

    def get_patients(self):
        episode_ids = self.get_patient_consultations().values_list(
            'episode_id', flat=True
        )

        return Patient.objects.filter(
            episode__id__in=episode_ids
        )

    def sort_rows(self, rows):
        episode_ids_by_when = list(self.get_patient_consultations().order_by(
            "-when"
        ).values_list('episode_id', flat=True))
        return sorted(rows, key=lambda x: episode_ids_by_when.index(x["episode"].id))

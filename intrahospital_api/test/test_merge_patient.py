import datetime
import json
import reversion
from unittest import mock
from django.apps import apps
from django.db import models as django_models
from django.utils import timezone
from django.contrib.auth.models import User
from elcid import models as elcid_models
from elcid import episode_categories
from plugins.admissions import models as admission_models
from plugins.appointments import models as appointment_models
from plugins.labtests import models as lab_models
from plugins.imaging import models as imaging_models
from plugins.tb import episode_categories as tb_episode_categories
from plugins.tb import models as tb_models
from opal.core.test import OpalTestCase
from opal import models as opal_models
from intrahospital_api import merge_patient
from reversion.models import Version


IGNORED_APPS = {
    "auth",
    "contenttypes",
    "sessions",
    "messages",
    "staticfiles",
    "humanize",
    "reversion",
    "rest_framework",
    "authtoken",
    "compressor",
    "admin",
    "django_celery_results",
}

PATIENT_RELATED_IGNORE_LIST = set([
    opal_models.Episode,
    # populated by load patient
    admission_models.Encounter,
    admission_models.PatientEncounterStatus,
    admission_models.TransferHistory,
    appointment_models.Appointment,
    appointment_models.PatientAppointmentStatus,
    imaging_models.Imaging,
    imaging_models.PatientImagingStatus,
    elcid_models.Demographics,
    elcid_models.MasterFileMeta,
    elcid_models.ContactInformation,
    elcid_models.GPDetails,
    elcid_models.NextOfKinDetails,

    # not used
    elcid_models.DuplicatePatient,
    lab_models.ObservationHistory,

    # part of the merge functionality
    elcid_models.MergedMRN,
])

EPISODE_RELATED_IGNORE_LIST = set([
    opal_models.Tagging,
])


class ModelMergeTestCase(OpalTestCase):
    def get_patient_episode_related_models(self):
        our_models = []
        for app_name, models in apps.all_models.items():
            if app_name not in IGNORED_APPS:
                our_models.extend(models.values())
        patient_related_models = set()
        episode_related_models = set()
        for model in our_models:
            for field in model._meta.fields:
                if isinstance(field, django_models.ForeignKey):
                    if field.related_model == opal_models.Patient:
                        patient_related_models.add(model)
                    elif field.related_model == opal_models.Episode:
                        episode_related_models.add(model)
        return patient_related_models, episode_related_models

    def test_episode_subrecords(self):
        """
        Checks that all models with an episode foreign key
        are either explicitly included by merge_patient.EPISODE_RELATED_MODELS
        or are explicitly excluded by EPISODE_RELATED_IGNORE_LIST
        """
        _, episode_related_models = self.get_patient_episode_related_models()
        for episode_related_model in episode_related_models:
            if episode_related_model not in EPISODE_RELATED_IGNORE_LIST:
                self.assertIn(
                    episode_related_model, merge_patient.EPISODE_RELATED_MODELS
                )

    def test_patient_subrecords(self):
        """
        Checks that all models with an episode foreign key
        are either explicitly included in merge_patient.PATIENT_RELATED_MODELS
        or merge_patient.STATUS_MODELS_TO_RELATED_MODEL
        or are explicitly excluded by PATIENT_RELATED_IGNORE_LIST
        """
        patient_related_models, _ = self.get_patient_episode_related_models()
        status_models = list(merge_patient.STATUS_MODELS_TO_RELATED_MODEL.keys())
        copied_patient_models = merge_patient.PATIENT_RELATED_MODELS + status_models
        for patient_related_model in patient_related_models:
            if patient_related_model not in PATIENT_RELATED_IGNORE_LIST:
                self.assertIn(
                    patient_related_model, copied_patient_models
                )


class UpdateTaggingTestCase(OpalTestCase):
    def setUp(self):
        _, self.old_episode = self.new_patient_and_episode_please()
        _, self.new_episode = self.new_patient_and_episode_please()
        self.old_user = User.objects.create(username="old_user")
        self.new_user = User.objects.create(username="new_user")

    def test_move_archived_tag(self):
        self.old_episode.tagging_set.create(
            archived=True, user=self.old_user, value="some list"
        )
        merge_patient.update_tagging(self.old_episode, self.new_episode)
        self.assertTrue(
            self.new_episode.tagging_set.filter(
                archived=True, user=self.old_user, value="some list"
            ).exists()
        )

    def test_move_active_tag(self):
        self.old_episode.tagging_set.create(
            archived=False, user=self.old_user, value="some list"
        )
        self.new_episode.tagging_set.create(
            archived=True, user=self.new_user, value="some list"
        )
        merge_patient.update_tagging(self.old_episode, self.new_episode)
        self.assertTrue(
            self.new_episode.tagging_set.filter(
                archived=False, user=self.old_user, value="some list"
            ).exists()
        )

    def test_does_not_move_archived_tag_if_active_tag_exists(self):
        self.old_episode.tagging_set.create(
            archived=True, user=self.old_user, value="some list"
        )
        self.new_episode.tagging_set.create(
            archived=False, user=self.new_user, value="some list"
        )
        merge_patient.update_tagging(self.old_episode, self.new_episode)
        self.assertTrue(
            self.new_episode.tagging_set.filter(
                archived=False, user=self.new_user, value="some list"
            ).exists()
        )

    def test_does_not_move_archived_tag_if_archived_tag_exists(self):
        self.old_episode.tagging_set.create(
            archived=True, user=self.old_user, value="some list"
        )
        self.new_episode.tagging_set.create(
            archived=True, user=self.new_user, value="some list"
        )
        merge_patient.update_tagging(self.old_episode, self.new_episode)
        self.assertTrue(
            self.new_episode.tagging_set.filter(
                archived=True, user=self.new_user, value="some list"
            ).exists()
        )

    def test_does_not_move_active_tag_if_active_tag_exists(self):
        self.old_episode.tagging_set.create(
            archived=False, user=self.old_user, value="some list"
        )
        self.new_episode.tagging_set.create(
            archived=False, user=self.new_user, value="some list"
        )
        merge_patient.update_tagging(self.old_episode, self.new_episode)
        self.assertTrue(
            self.new_episode.tagging_set.filter(
                archived=False, user=self.new_user, value="some list"
            ).exists()
        )


class UpdateSingletonTestCase(OpalTestCase):
    def setUp(self):
        self.old_patient, self.old_episode = self.new_patient_and_episode_please()
        self.old_mrn = "123"
        self.old_patient.demographics_set.update(hospital_number=self.old_mrn)
        self.new_patient, self.new_episode = self.new_patient_and_episode_please()
        self.new_mrn = "456"
        self.new_patient.demographics_set.update(hospital_number=self.new_mrn)

    def test_simple_update_episode_singleton(self):
        """
        The new episode subrecord has not been edited
        the old one has.

        We expect the old singleton to replace the new
        singleton.
        """
        old_location = self.old_episode.location_set.get()
        old_location.hospital = "Some hospital"
        old_location.updated = timezone.now()
        old_location.save()
        merge_patient.update_singleton(
            elcid_models.Location, self.old_episode, self.new_episode, self.old_mrn
        )
        new_location = self.new_episode.location_set.get()
        self.assertEqual(new_location.hospital, "Some hospital")
        self.assertEqual(new_location.previous_mrn, self.old_mrn)

    def test_simple_update_patient_singleton(self):
        """
        The new patient subrecord has not been edited
        the old one has.

        We expect the old singleton to replace the new
        singleton.
        """
        old_nationality = self.old_patient.nationality_set.get()
        old_nationality.arrival_in_the_uk = "2020"
        old_nationality.updated = timezone.now()
        old_nationality.save()
        merge_patient.update_singleton(
            tb_models.Nationality,
            self.old_patient,
            self.new_patient,
            self.old_mrn,
        )
        new_nationality = self.new_patient.nationality_set.get()
        self.assertEqual(new_nationality.arrival_in_the_uk, "2020")
        self.assertEqual(new_nationality.previous_mrn, self.old_mrn)

    def test_update_singleton_only_new_updated(self):
        """
        The new episode subrecord has been edited
        the old one has not.

        We expect nothing to happen.
        """
        with reversion.create_revision():
            new_location = self.new_episode.location_set.get()
            new_location.hospital = "Some hospital"
            new_location.updated = timezone.now()
            new_location.save()
        old_location = self.old_episode.location_set.get()
        merge_patient.update_singleton(
            elcid_models.Location,
            self.old_episode,
            self.new_episode,
            self.old_mrn,
        )
        self.assertIsNone(old_location.previous_mrn)
        version = Version.objects.get_for_object(new_location).get()
        self.assertEqual(version.field_dict["hospital_ft"], "Some hospital")

    def test_older_is_more_recent_than_new(self):
        """
        The inactive MRNs data is more recent
        than the active MRNs data.

        Update the active MRNs data and make
        sure there is a reference in the version
        history
        """
        # we create a reversion as thats what the behavour
        # expected in prod.
        with reversion.create_revision():
            new_nationality = self.new_patient.nationality_set.get()
            new_nationality.arrival_in_the_uk = "2020"
            new_nationality.updated = timezone.now() - datetime.timedelta(1)
            new_nationality.save()
        old_nationality = self.old_patient.nationality_set.get()
        old_nationality.arrival_in_the_uk = "2021"
        old_nationality.updated = timezone.now()
        old_nationality.save()
        merge_patient.update_singleton(
            tb_models.Nationality, self.old_patient, self.new_patient, self.old_mrn
        )
        new_nationality.refresh_from_db()
        self.assertEqual(new_nationality.previous_mrn, self.old_mrn)
        self.assertEqual(new_nationality.arrival_in_the_uk, "2021")
        # Version is by default ordered by -id
        previous_version = (
            Version.objects.get_for_object(new_nationality).order_by("id").first()
        )
        self.assertEqual(previous_version.field_dict["arrival_in_the_uk"], "2020")
        self.assertIsNone(previous_version.field_dict["previous_mrn"])

    def test_newer_is_more_recent_than_old(self):
        """
        The active MRNs data is more recent
        than the inactive MRNs data.

        Update the active MRNs data with a record
        of the last inactive data for the version
        history, then restore the most recent data.
        """
        # we create a reversion as thats what the behavour
        # expected in prod.
        with reversion.create_revision():
            new_nationality = self.new_patient.nationality_set.get()
            new_nationality.arrival_in_the_uk = "2020"
            new_nationality.updated = timezone.now()
            new_nationality.save()
        old_nationality = self.old_patient.nationality_set.get()
        old_nationality.arrival_in_the_uk = "2021"
        old_nationality.updated = timezone.now() - datetime.timedelta(1)
        old_nationality.save()
        merge_patient.update_singleton(
            tb_models.Nationality,
            self.old_patient,
            self.new_patient,
            self.old_mrn,
        )
        new_nationality.refresh_from_db()
        self.assertIsNone(new_nationality.previous_mrn)
        self.assertEqual(new_nationality.arrival_in_the_uk, "2020")
        # Version is by default ordered by -id
        # A new one is created on each save so we expect
        # there to be 3 versions
        # 1. The initial creation
        # 2. The updated with the old values and the previous MRN
        # 3. The current version
        previous_versions = Version.objects.get_for_object(new_nationality).order_by(
            "id"
        )
        self.assertEqual(previous_versions[0].field_dict["arrival_in_the_uk"], "2020")
        self.assertEqual(previous_versions[0].field_dict["previous_mrn"], None)
        self.assertEqual(previous_versions[1].field_dict["arrival_in_the_uk"], "2021")
        self.assertEqual(previous_versions[1].field_dict["previous_mrn"], self.old_mrn)
        self.assertEqual(previous_versions[2].field_dict["arrival_in_the_uk"], "2020")
        self.assertEqual(previous_versions[2].field_dict["previous_mrn"], None)


class MoveNonSingletonsTestCase(OpalTestCase):
    def setUp(self):
        self.old_patient, self.old_episode = self.new_patient_and_episode_please()
        self.old_mrn = "123"
        self.old_patient.demographics_set.update(hospital_number=self.old_mrn)
        self.new_patient, self.new_episode = self.new_patient_and_episode_please()
        self.new_mrn = "456"
        self.new_patient.demographics_set.update(hospital_number=self.new_mrn)

    def test_copies_episode_related_records(self):
        """
        Test move_non_singletons copys over non singleton episode subrecords
        """
        self.old_episode.antimicrobial_set.create(no_antimicrobials=True)
        merge_patient.move_non_singletons(
            elcid_models.Antimicrobial,
            self.old_episode,
            self.new_episode,
            self.old_mrn,
        )
        new_antimicobiral = self.new_episode.antimicrobial_set.get()
        self.assertTrue(new_antimicobiral.no_antimicrobials)
        self.assertTrue(new_antimicobiral.previous_mrn, self.old_mrn)

    def test_copies_patient_related_records(self):
        """
        Test move_non_singletons copys over non singleton patient subrecords
        """
        risk_factor = self.old_patient.riskfactor_set.create()
        risk_factor.risk_factor = "On immunosupressants"
        risk_factor.save()
        merge_patient.move_non_singletons(
            elcid_models.RiskFactor,
            self.old_patient,
            self.new_patient,
            self.old_mrn,
        )
        risk_factor = self.new_patient.riskfactor_set.get()
        self.assertEqual(risk_factor.risk_factor, "On immunosupressants")
        self.assertTrue(risk_factor.previous_mrn, self.old_mrn)


class MoveRelatedRecordTestCase(OpalTestCase):
    def setUp(self):
        self.old_patient, self.old_episode = self.new_patient_and_episode_please()
        self.old_mrn = "123"
        self.old_patient.demographics_set.update(hospital_number=self.old_mrn)
        self.new_patient, self.new_episode = self.new_patient_and_episode_please()
        self.new_mrn = "456"
        self.new_patient.demographics_set.update(hospital_number=self.new_mrn)

    def test_patient_singleton(self):
        """
        Test copy_subrecord copys over singleton patient subrecords
        """
        old_nationality = self.old_patient.nationality_set.get()
        old_nationality.arrival_in_the_uk = "2020"
        old_nationality.updated = timezone.now()
        old_nationality.save()
        merge_patient.move_record(
            tb_models.Nationality,
            self.old_patient,
            self.new_patient,
            self.old_mrn,
        )
        new_nationality = self.new_patient.nationality_set.get()
        self.assertEqual(new_nationality.arrival_in_the_uk, "2020")
        self.assertEqual(new_nationality.previous_mrn, self.old_mrn)

    def test_lab_tests(self):
        lab_test = self.old_patient.lab_tests.create(
            test_name="Blood culture",
            lab_number="123"
        )
        lab_test.observation_set.create(
            observation_name="WBC",
            observation_value="234"
        )
        merge_patient.move_record(
            lab_models.LabTest,
            self.old_patient,
            self.new_patient,
            self.old_mrn,
        )
        self.assertTrue(
            lab_models.Observation.objects.filter(
                test__patient_id=self.new_patient.id
            ).exists()
        )


    def test_episode_non_singleton(self):
        """
        Test copy_subrecord copys over non-singleton episode subrecords
        """
        self.old_episode.antimicrobial_set.create(no_antimicrobials=True)
        merge_patient.move_record(
            elcid_models.Antimicrobial,
            self.old_episode,
            self.new_episode,
            self.old_mrn,
        )
        new_antimicobiral = self.new_episode.antimicrobial_set.get()
        self.assertTrue(new_antimicobiral.no_antimicrobials)
        self.assertTrue(new_antimicobiral.previous_mrn, self.old_mrn)


class UpdateStatusesTestCase(OpalTestCase):
    def setUp(self):
        self.new_patient, _ = self.new_patient_and_episode_please()

    def test_discharge_summary_status(self):
        self.new_patient.dischargesummaries.create()
        merge_patient.updates_statuses(self.new_patient)
        summary_status = self.new_patient.patientdischargesummarystatus_set.get()
        self.assertTrue(summary_status.has_dischargesummaries)
        amt_handover_status = self.new_patient.patientamthandoverstatus_set.get()
        self.assertFalse(amt_handover_status.has_handover)
        nursing_status = self.new_patient.patientnursinghandoverstatus_set.get()
        self.assertFalse(nursing_status.has_handover)

    def test_amt_handover_status(self):
        self.new_patient.amt_handover.create(sqlserver_id=1, handover_version=1)
        merge_patient.updates_statuses(self.new_patient)
        summary_status = self.new_patient.patientdischargesummarystatus_set.get()
        self.assertFalse(summary_status.has_dischargesummaries)
        amt_handover_status = self.new_patient.patientamthandoverstatus_set.get()
        self.assertTrue(amt_handover_status.has_handover)
        nursing_status = self.new_patient.patientnursinghandoverstatus_set.get()
        self.assertFalse(nursing_status.has_handover)

    def test_nursing_handover_status(self):
        self.new_patient.nursing_handover.create(
            sqlserver_uniqueid=1, database_version=1
        )
        merge_patient.updates_statuses(self.new_patient)
        summary_status = self.new_patient.patientdischargesummarystatus_set.get()
        self.assertFalse(summary_status.has_dischargesummaries)
        amt_handover_status = self.new_patient.patientamthandoverstatus_set.get()
        self.assertFalse(amt_handover_status.has_handover)
        nursing_status = self.new_patient.patientnursinghandoverstatus_set.get()
        self.assertTrue(nursing_status.has_handover)


@mock.patch('intrahospital_api.merge_patient.loader.load_patient')
@mock.patch('intrahospital_api.merge_patient.append_to_merge_file')
class MergePatientTestCase(OpalTestCase):
    def setUp(self):
        self.old_patient, self.old_episode = self.new_patient_and_episode_please()
        self.old_mrn = "123"
        self.old_patient.demographics_set.update(hospital_number=self.old_mrn)
        self.old_episode.category_name = (
            episode_categories.InfectionService.display_name
        )
        self.old_episode.save()
        self.new_patient, self.new_episode = self.new_patient_and_episode_please()
        self.new_episode.category_name = (
            episode_categories.InfectionService.display_name
        )
        self.new_episode.save()
        self.new_mrn = "456"
        self.new_patient.demographics_set.update(hospital_number=self.new_mrn)
        # The logging expects a user with username ohc
        User.objects.create(username='ohc')

    def test_writing_to_merge_log(self, append_to_merge_file, load_patient):
        self.new_patient.mergedmrn_set.create(mrn=self.old_mrn)
        old_id = self.old_patient.id
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        self.assertEqual(self.new_patient.mergedmrn_set.count(), 1)
        self.assertIsNotNone(
            self.new_patient.mergedmrn_set.get(mrn=self.old_mrn).our_merge_datetime
        )
        log_call_args = append_to_merge_file.call_args_list
        self.assertEqual(len(log_call_args), 7)
        old_json = json.loads(log_call_args[2][0][0])
        self.assertEqual(old_json['id'], old_id)
        new_json = json.loads(log_call_args[4][0][0])
        self.assertEqual(new_json['id'], self.new_patient.id)
        merged_json = json.loads(log_call_args[6][0][0])
        self.assertEqual(merged_json['id'], self.new_patient.id)

    def test_copies_over_patient_subrecords(self, append_to_merge_file, load_patient):
        """
        Test merge_patient copies over patient subrecords to
        the new patient
        """
        self.new_patient.mergedmrn_set.create(mrn=self.old_mrn)
        old_nationality = self.old_patient.nationality_set.get()
        old_nationality.arrival_in_the_uk = "2020"
        old_nationality.updated = timezone.now()
        old_nationality.save()
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        new_nationality = self.new_patient.nationality_set.get()
        self.assertEqual(new_nationality.arrival_in_the_uk, "2020")
        self.assertEqual(new_nationality.previous_mrn, self.old_mrn)
        self.assertEqual(self.new_patient.mergedmrn_set.count(), 1)
        self.assertIsNotNone(
            self.new_patient.mergedmrn_set.get(mrn=self.old_mrn).our_merge_datetime
        )
        log_call_args = append_to_merge_file.call_args_list
        self.assertEqual(len(log_call_args), 7)

    def test_copies_over_episode_subrecords_where_the_episode_exists(self, append_to_merge_file, load_patient):
        """
        Test merge_patient copies over episode subrecords to
        the episode
        """
        self.old_episode.microbiologyinput_set.create(
            clinical_discussion="treatment options"
        )
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        # make sure we haven't created a new episode
        self.assertEqual(self.new_patient.episode_set.count(), 1)
        micro_input = self.new_episode.microbiologyinput_set.get()
        self.assertEqual(micro_input.clinical_discussion, "treatment options")

    def test_copies_over_observations(self, append_to_merge_file, load_patient):
        self.old_episode.observation_set.create()
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        self.assertTrue(self.new_episode.observation_set.exists())

    def test_copies_over_episode_subrecords_where_the_episode_does_not_exist(self, append_to_merge_file, load_patient):
        """
        Test merge_patient creates episode categories if they
        don't exist
        """
        tb_category = tb_episode_categories.TbEpisode.display_name
        old_tb_episode = self.old_patient.episode_set.create(category_name=tb_category)
        old_tb_episode.patientconsultation_set.create(plan="treatment options")
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        new_tb_episode = self.new_patient.episode_set.get(category_name=tb_category)
        new_patient_consultation = new_tb_episode.patientconsultation_set.get()
        self.assertEqual(new_patient_consultation.plan, "treatment options")

    def test_blood_cultures(self, append_to_merge_file, load_patient):
        """
        Blood cultures have related foreign keys, make sure that
        these are copied over
        """
        blood_culture = self.old_patient.bloodcultureset_set.create(lab_number="111")
        blood_culture.isolates.create(date_positive=datetime.date.today())
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        blood_culture = self.new_patient.bloodcultureset_set.get()
        self.assertEqual(blood_culture.lab_number, "111")
        self.assertEqual(
            blood_culture.isolates.get().date_positive, datetime.date.today()
        )

    def test_updates_status(self, append_to_merge_file, load_patient):
        self.old_patient.dischargesummaries.create()
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        self.assertTrue(self.new_patient.dischargesummaries.exists())
        summary_status = self.new_patient.patientdischargesummarystatus_set.get()
        self.assertTrue(summary_status.has_dischargesummaries)

    def test_copies_tags(self, append_to_merge_file, load_patient):
        self.old_episode.tagging_set.create(archived=False, value="some list")
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        self.assertTrue(
            self.new_episode.tagging_set.filter(
                archived=False, value="some list"
            ).exists()
        )

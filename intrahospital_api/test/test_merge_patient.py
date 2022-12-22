import datetime
import reversion
from elcid import models
from elcid import episode_categories
from plugins.tb import episode_categories as tb_episode_categories
from plugins.tb import models as tb_models
from opal.core.test import OpalTestCase
from intrahospital_api import merge_patient
from django.utils import timezone
from django.contrib.auth.models import User
from reversion.models import Version


class CopyTaggingTestCase(OpalTestCase):
    def setUp(self):
        _, self.old_episode = self.new_patient_and_episode_please()
        _, self.new_episode = self.new_patient_and_episode_please()
        self.old_user = User.objects.create(username='old_user')
        self.new_user = User.objects.create(username='new_user')

    def test_copy_archived_tag(self):
        self.old_episode.tagging_set.create(
            archived=True,
            user=self.old_user,
            value="some list"
        )
        merge_patient.copy_tagging(self.old_episode, self.new_episode)
        self.assertTrue(
            self.new_episode.tagging_set.filter(
                archived=True, user=self.old_user, value="some list"
            ).exists()
        )

    def test_copy_active_tag(self):
        self.old_episode.tagging_set.create(
            archived=False,
            user=self.old_user,
            value="some list"
        )
        self.new_episode.tagging_set.create(
            archived=True,
            user=self.new_user,
            value="some list"
        )
        merge_patient.copy_tagging(self.old_episode, self.new_episode)
        self.assertTrue(
            self.new_episode.tagging_set.filter(
                archived=False, user=self.old_user, value="some list"
            ).exists()
        )

    def test_does_not_copy_archived_tag_if_active_tag_exists(self):
        self.old_episode.tagging_set.create(
            archived=True,
            user=self.old_user,
            value="some list"
        )
        self.new_episode.tagging_set.create(
            archived=False,
            user=self.new_user,
            value="some list"
        )
        merge_patient.copy_tagging(self.old_episode, self.new_episode)
        self.assertTrue(
            self.new_episode.tagging_set.filter(
                archived=False, user=self.new_user, value="some list"
            ).exists()
        )

    def test_does_not_copy_archived_tag_if_archived_tag_exists(self):
        self.old_episode.tagging_set.create(
            archived=True,
            user=self.old_user,
            value="some list"
        )
        self.new_episode.tagging_set.create(
            archived=True,
            user=self.new_user,
            value="some list"
        )
        merge_patient.copy_tagging(self.old_episode, self.new_episode)
        self.assertTrue(
            self.new_episode.tagging_set.filter(
                archived=True, user=self.new_user, value="some list"
            ).exists()
        )

    def test_does_not_copy_active_tag_if_active_tag_exists(self):
        self.old_episode.tagging_set.create(
            archived=False,
            user=self.old_user,
            value="some list"
        )
        self.new_episode.tagging_set.create(
            archived=False,
            user=self.new_user,
            value="some list"
        )
        merge_patient.copy_tagging(self.old_episode, self.new_episode)
        self.assertTrue(
            self.new_episode.tagging_set.filter(
                archived=False, user=self.new_user, value="some list"
            ).exists()
        )


class UpdateSingletonTestCase(OpalTestCase):
    def setUp(self):
        self.old_patient, self.old_episode = self.new_patient_and_episode_please()
        self.old_mrn = "123"
        self.old_patient.demographics_set.update(
            hospital_number=self.old_mrn
        )
        self.new_patient, self.new_episode = self.new_patient_and_episode_please()
        self.new_mrn = "456"
        self.new_patient.demographics_set.update(
            hospital_number=self.new_mrn
        )

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
            old_location,
            self.new_episode,
            self.old_mrn,
            self.new_mrn,
            is_episode_subrecord=True
        )
        new_location = self.new_episode.location_set.get()
        self.assertEqual(
            new_location.hospital, "Some hospital"
        )
        self.assertEqual(
            new_location.previous_mrn, self.old_mrn
        )

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
            old_nationality,
            self.new_patient,
            self.old_mrn,
            self.new_mrn,
            is_episode_subrecord=False
        )
        new_nationality = self.new_patient.nationality_set.get()
        self.assertEqual(
            new_nationality.arrival_in_the_uk, "2020"
        )
        self.assertEqual(
            new_nationality.previous_mrn, self.old_mrn
        )


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
            old_location,
            self.new_episode,
            self.old_mrn,
            self.new_mrn,
            is_episode_subrecord=True
        )
        self.assertIsNone(old_location.previous_mrn)
        version = Version.objects.get_for_object(new_location).get()
        self.assertEqual(
            version.field_dict["hospital_ft"], "Some hospital"
        )

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
            old_nationality,
            self.new_patient,
            self.old_mrn,
            self.new_mrn,
            is_episode_subrecord=False
        )
        new_nationality.refresh_from_db()
        self.assertEqual(new_nationality.previous_mrn, self.old_mrn)
        self.assertEqual(new_nationality.arrival_in_the_uk, "2021")
        # Version is by default ordered by -id
        previous_version = Version.objects.get_for_object(new_nationality).order_by('id').first()
        self.assertEqual(
            previous_version.field_dict["arrival_in_the_uk"], "2020"
        )
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
            old_nationality,
            self.new_patient,
            self.old_mrn,
            self.new_mrn,
            is_episode_subrecord=False
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
        previous_versions = Version.objects.get_for_object(new_nationality).order_by('id')
        self.assertEqual(
            previous_versions[0].field_dict["arrival_in_the_uk"], "2020"
        )
        self.assertEqual(
            previous_versions[0].field_dict["previous_mrn"], None
        )
        self.assertEqual(
            previous_versions[1].field_dict["arrival_in_the_uk"], "2021"
        )
        self.assertEqual(
            previous_versions[1].field_dict["previous_mrn"], self.old_mrn
        )
        self.assertEqual(
            previous_versions[2].field_dict["arrival_in_the_uk"], "2020"
        )
        self.assertEqual(
            previous_versions[2].field_dict["previous_mrn"], None
        )

class CopyNonSingletonsTestCase(OpalTestCase):
    def setUp(self):
        self.old_patient, self.old_episode = self.new_patient_and_episode_please()
        self.old_mrn = "123"
        self.old_patient.demographics_set.update(
            hospital_number=self.old_mrn
        )
        self.new_patient, self.new_episode = self.new_patient_and_episode_please()
        self.new_mrn = "456"
        self.new_patient.demographics_set.update(
            hospital_number=self.new_mrn
        )

    def test_copies_episode_related_records(self):
        """
        Test copy_non_singletons copys over non singleton episode subrecords
        """
        self.old_episode.antimicrobial_set.create(
            no_antimicrobials=True
        )
        merge_patient.copy_non_singletons(
            self.old_episode.antimicrobial_set.all(),
            self.new_episode,
            self.old_mrn,
            is_episode_subrecord=True
        )
        new_antimicobiral = self.new_episode.antimicrobial_set.get()
        self.assertTrue(new_antimicobiral.no_antimicrobials)
        self.assertTrue(new_antimicobiral.previous_mrn, self.old_mrn)

    def test_copies_patient_related_records(self):
        """
        Test copy_non_singletons copys over non singleton patient subrecords
        """
        risk_factor = self.old_patient.riskfactor_set.create()
        risk_factor.risk_factor = "On immunosupressants"
        risk_factor.save()
        merge_patient.copy_non_singletons(
            self.old_patient.riskfactor_set.all(),
            self.new_patient,
            self.old_mrn,
            is_episode_subrecord=False
        )
        risk_factor = self.new_patient.riskfactor_set.get()
        self.assertEqual(risk_factor.risk_factor, "On immunosupressants")
        self.assertTrue(risk_factor.previous_mrn, self.old_mrn)


class CopyRelatedRecordTestCase(OpalTestCase):
    def setUp(self):
        self.old_patient, self.old_episode = self.new_patient_and_episode_please()
        self.old_mrn = "123"
        self.old_patient.demographics_set.update(
            hospital_number=self.old_mrn
        )
        self.new_patient, self.new_episode = self.new_patient_and_episode_please()
        self.new_mrn = "456"
        self.new_patient.demographics_set.update(
            hospital_number=self.new_mrn
        )

    def test_patient_singleton(self):
        """
        Test copy_subrecord copys over singleton patient subrecords
        """
        old_nationality = self.old_patient.nationality_set.get()
        old_nationality.arrival_in_the_uk = "2020"
        old_nationality.updated = timezone.now()
        old_nationality.save()
        merge_patient.copy_record(
            tb_models.Nationality,
            self.old_patient,
            self.new_patient,
            self.old_mrn,
            self.new_mrn,
            is_episode_subrecord=False
        )
        new_nationality = self.new_patient.nationality_set.get()
        self.assertEqual(
            new_nationality.arrival_in_the_uk, "2020"
        )
        self.assertEqual(
            new_nationality.previous_mrn, self.old_mrn
        )

    def test_episode_non_singleton(self):
        """
        Test copy_subrecord copys over non-singleton episode subrecords
        """
        self.old_episode.antimicrobial_set.create(
            no_antimicrobials=True
        )
        merge_patient.copy_record(
            models.Antimicrobial,
            self.old_episode,
            self.new_episode,
            self.old_mrn,
            self.new_mrn,
            is_episode_subrecord=True
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


class MergePatientTestCase(OpalTestCase):
    def setUp(self):
        self.old_patient, self.old_episode = self.new_patient_and_episode_please()
        self.old_mrn = "123"
        self.old_patient.demographics_set.update(
            hospital_number=self.old_mrn
        )
        self.old_episode.category_name = episode_categories.InfectionService.display_name
        self.old_episode.save()
        self.new_patient, self.new_episode = self.new_patient_and_episode_please()
        self.new_episode.category_name = episode_categories.InfectionService.display_name
        self.new_episode.save()
        self.new_mrn = "456"
        self.new_patient.demographics_set.update(
            hospital_number=self.new_mrn
        )

    def test_copies_over_patient_subrecords(self):
        """
        Test merge_patient copies over patient subrecords to
        the new patient
        """
        self.new_patient.mergedmrn_set.create(
            mrn=self.old_mrn
        )
        old_nationality = self.old_patient.nationality_set.get()
        old_nationality.arrival_in_the_uk = "2020"
        old_nationality.updated = timezone.now()
        old_nationality.save()
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        new_nationality = self.new_patient.nationality_set.get()
        self.assertEqual(
            new_nationality.arrival_in_the_uk, "2020"
        )
        self.assertEqual(
            new_nationality.previous_mrn, self.old_mrn
        )
        self.assertEqual(
            self.new_patient.mergedmrn_set.count(), 1
        )
        self.assertIsNotNone(
            self.new_patient.mergedmrn_set.get(mrn=self.old_mrn).our_merge_datetime
        )

    def test_copies_over_episode_subrecords_where_the_episode_exists(self):
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

    def test_copies_over_episode_subrecords_where_the_episode_does_not_exist(self):
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

    def test_blood_cultures(self):
        """
        Blood cultures have related foreign keys, make sure that
        these are copied over
        """
        blood_culture = self.old_patient.bloodcultureset_set.create(
            lab_number="111"
        )
        blood_culture.isolates.create(
            date_positive=datetime.date.today()
        )
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        blood_culture = self.new_patient.bloodcultureset_set.get()
        self.assertEqual(blood_culture.lab_number, "111")
        self.assertEqual(
            blood_culture.isolates.get().date_positive, datetime.date.today()
        )

    def test_updates_status(self):
        self.old_patient.dischargesummaries.create()
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        self.assertTrue(
            self.new_patient.dischargesummaries.exists()
        )
        summary_status = self.new_patient.patientdischargesummarystatus_set.get()
        self.assertTrue(summary_status.has_dischargesummaries)

    def test_copies_tags(self):
        self.old_episode.tagging_set.create(archived=False, value='some list')
        merge_patient.merge_patient(
            old_patient=self.old_patient, new_patient=self.new_patient
        )
        self.assertTrue(
            self.new_episode.tagging_set.filter(archived=False, value='some list').exists()
        )

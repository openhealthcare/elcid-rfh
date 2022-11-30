import datetime
from unittest import mock
from django.test import TestCase
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from elcid import episode_categories

from opal.core import exceptions
from opal.core.test import OpalTestCase
from opal.models import (
    Patient, Episode, Condition, Synonym, Antimicrobial
)
from elcid import models as emodels
from obs import models as obs_models


class AbstractPatientTestCase(TestCase):
    def setUp(self):
        super(AbstractPatientTestCase, self).setUp()
        self.patient = Patient()
        self.patient.save()
        self.patient.demographics_set.update(
            consistency_token="12345678",
            first_name="John",
            surname="Smith",
            hospital_number="AA1111",
            date_of_birth="1972-06-20",
        )
        self.demographics = self.patient.demographics_set.get()


class AbstractEpisodeTestCase(AbstractPatientTestCase):
    def setUp(self):
        super(AbstractEpisodeTestCase, self).setUp()
        self.episode = Episode.objects.create(
            patient=self.patient,
            consistency_token="12345675"
        )


class DemographicsTest(OpalTestCase, AbstractPatientTestCase):

    def test_to_dict(self):
        expected_data = {
            'consistency_token': '12345678',
            'patient_id': self.patient.id,
            'id': self.demographics.id,
            'first_name': 'John',
            'surname': 'Smith',
            'middle_name': None,
            'title': '',
            'marital_status': u'',
            'main_language': None,
            'nationality': None,
            'religion': None,
            'created': None,
            'updated': None,
            'created_by_id': None,
            'updated_by_id': None,
            'date_of_birth': datetime.date(1972, 6, 20),
            'birth_place': '',
            'ethnicity': u'',
            'sex': '',
            'hospital_number': 'AA1111',
            'nhs_number': None,
            'date_of_death': None,
            'death_indicator': False,
            'post_code': None,
            'gp_practice_code': None,
            'external_system': None,
            'external_identifier': None
        }
        self.assertEqual(expected_data, self.demographics.to_dict(self.user))

    def test_update_from_dict(self):
        data = {
            'consistency_token': '12345678',
            'id': self.demographics.id,
            'first_name': 'Johann',
            'surname': 'Schmidt',
            'date_of_birth': '21/6/1972',
            'hospital_number': 'AA1112',
            }
        self.demographics.update_from_dict(data, self.user)
        demographics = self.patient.demographics_set.get()

        self.assertEqual('Johann', demographics.first_name)
        self.assertEqual('Schmidt', demographics.surname)
        self.assertEqual(datetime.date(1972, 6, 21), demographics.date_of_birth)
        self.assertEqual('AA1112', demographics.hospital_number)

    def test_update_from_dict_with_missing_consistency_token(self):
        with self.assertRaises(exceptions.MissingConsistencyTokenError):
            self.demographics.update_from_dict({}, self.user)

    def test_update_from_dict_with_incorrect_consistency_token(self):
        with self.assertRaises(exceptions.ConsistencyError):
            self.demographics.update_from_dict(
                {'consistency_token': '87654321'}, self.user
            )


class OriginalMRNTestCase(OpalTestCase):
    def setUp(self):
        _, self.episode = self.new_patient_and_episode_please()
        self.procedure = self.episode.procedure_set.create()

    def test_nones_original_mrn_on_update(self):
        self.procedure.original_mrn = "123"
        self.procedure.stage = "Stage 1"
        self.procedure.save()
        self.procedure.update_from_dict({'stage': 'Stage 2'}, None)
        procedure = self.episode.procedure_set.get()
        self.assertEqual(
            procedure.stage, "Stage 2"
        )
        self.assertIsNone(procedure.original_mrn)

    def test_does_not_error_if_original_mrn_is_none(self):
        self.procedure.stage = "Stage 1"
        self.procedure.save()
        self.procedure.update_from_dict({'stage': 'Stage 2'}, None)
        procedure = self.episode.procedure_set.get()
        self.assertEqual(
            procedure.stage, "Stage 2"
        )
        self.assertIsNone(procedure.original_mrn)


class LocationTest(OpalTestCase, AbstractEpisodeTestCase):

    def setUp(self):
        super(LocationTest, self).setUp()

        self.location = emodels.Location.objects.create(
            bed="13",
            consistency_token="12345678",
            hospital="UCH",
            ward="T10",
            episode=self.episode
        )

    def test_to_dict(self):
        expected_data = {
            'consistency_token': '12345678',
            'consultant': None,
            'episode_id': self.episode.id,
            'id': self.location.id,
            'hospital': 'UCH',
            'ward': 'T10',
            'bed': '13',
            'original_mrn': None,
            'created': None,
            'updated': None,
            'updated_by_id': None,
            'created_by_id': None,
            'provenance': '',
            'unit': None,
            }
        result = {str(k): v for k, v in self.location.to_dict(self.user).items()}
        self.assertEqual(expected_data, result)

    def test_update_from_dict(self):
        data = {
            'consistency_token': '12345678',
            'id': self.location.id,
            'hospital': 'HH',
            'ward': 'T10',
            'bed': '13',
            }
        self.location.update_from_dict(data, self.user)
        self.assertEqual('HH', self.location.hospital)


class GetForLookupListTestCase(OpalTestCase):
    def setUp(self):
        self.antimicrobial_1 = Antimicrobial.objects.create(
            name="antimicrobial_1",
        )

        self.antimicrobial_2 = Antimicrobial.objects.create(
            name="antimicrobial_2",
        )

        self.antimicrobial_3 = Antimicrobial.objects.create(
            name="antimicrobial_3",
        )

        antimicrobial_content_type = ContentType.objects.get_for_model(
            Antimicrobial
        )

        self.synonym_1 = Synonym.objects.get_or_create(
            content_type=antimicrobial_content_type,
            object_id=self.antimicrobial_2.id,
            name="synonym_1"
        )

        self.synonym_2 = Synonym.objects.get_or_create(
            content_type=antimicrobial_content_type,
            object_id=self.antimicrobial_3.id,
            name="synonym_2"
        )

        # make sure content type querying works
        # lets add in an item with a different content type but the same name
        self.synonym_3 = Synonym.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(Condition),
            object_id=self.antimicrobial_3.id,
            name="synonym_2"
        )

    def test_translate_to_models(self):
        models = emodels.get_for_lookup_list(
            Antimicrobial,
            [
                "antimicrobial_1", "antimicrobial_2", "antimicrobial_3",
                "synonym_1", "synonym_2"
            ]
        )
        self.assertEqual(
            set(models),
            set([
                self.antimicrobial_1,
                self.antimicrobial_2,
                self.antimicrobial_3
            ])
        )

    def test_does_synonym_lookups(self):
        models = emodels.get_for_lookup_list(
            Antimicrobial,
            [
                "synonym_1", "synonym_2"
            ]
        )
        self.assertEqual(
            set(models),
            set([
                self.antimicrobial_2,
                self.antimicrobial_3
            ])
        )

class MicrobiologyInputTestCase(OpalTestCase):
    def setUp(self):
        self.patient, self.episode = self.new_patient_and_episode_please()

    def test_update_from_dict_create_micro_relation(self):
        update_dict = {
            'when': '27/03/2020 09:33:55',
            'initials': 'FJK',
            'infection_control': 'asdf',
            'clinical_discussion': 'asdf',
            'reason_for_interaction': 'ICU round',
            'micro_input_icu_round_relation': {
                'observation': {'temperature': 1111},
                'icu_round': {}
            },
            'episode_id': self.episode.id
        }
        micro_input = emodels.MicrobiologyInput(
            episode=self.episode
        )
        micro_input.update_from_dict(update_dict, self.user)
        saved_input = self.episode.microbiologyinput_set.get()
        saved_input.refresh_from_db()
        observation = saved_input.microinputicuroundrelation.observation
        self.assertEqual(
            observation.temperature, 1111
        )
        # observatio should gain the datetime
        # of the advice
        self.assertEqual(
            observation.datetime,
            timezone.make_aware(datetime.datetime(
                2020, 3, 27, 9, 33, 55
            ))
        )
        self.assertEqual(
            saved_input.microinputicuroundrelation.icu_round.id,
            emodels.ICURound.objects.get().id
        )

    def test_update_from_dict_zeros_original_mrn(self):
        update_dict = {
            'when': '27/03/2020 09:33:55',
            'initials': 'FJK',
            'infection_control': 'asdf',
            'clinical_discussion': 'asdf',
            'reason_for_interaction': 'ICU round',
            'micro_input_icu_round_relation': {
                'observation': {'temperature': 1111},
                'icu_round': {}
            },
            'episode_id': self.episode.id
        }
        micro_input = emodels.MicrobiologyInput(
            episode=self.episode, original_mrn="123"
        )
        micro_input.update_from_dict(update_dict, self.user)
        saved_input = self.episode.microbiologyinput_set.get()
        self.assertEqual(
            saved_input.original_mrn, None
        )


    def test_update_from_dict_without_when(self):
        update_dict = {
            'initials': 'FJK',
            'infection_control': 'asdf',
            'clinical_discussion': 'asdf',
            'reason_for_interaction': 'ICU round',
            'micro_input_icu_round_relation': {
                'observation': {'temperature': 1111},
                'icu_round': {}
            },
            'episode_id': self.episode.id
        }
        micro_input = emodels.MicrobiologyInput(
            episode=self.episode
        )
        micro_input.update_from_dict(update_dict, self.user)

        # refesh from database
        micro_input = self.episode.microbiologyinput_set.get()

        self.assertEqual(None, micro_input.when)
        self.assertEqual(None, micro_input.microinputicuroundrelation.icu_round.when)


    def test_update_from_dict_micro_relation(self):
        micro_input = emodels.MicrobiologyInput.objects.create(
            episode=self.episode
        )
        observation =  obs_models.Observation.objects.create(
            episode=self.episode,
            temperature=111,
            datetime=timezone.make_aware(datetime.datetime(
                2020, 3, 26, 10, 33, 55
            ))
        )
        icu_round = emodels.ICURound.objects.create(
            episode=self.episode,
            when=timezone.make_aware(datetime.datetime(
                2020, 3, 26, 10, 33, 55
            )),
            sofa_score='12'
        )
        emodels.MicroInputICURoundRelation.objects.create(
            microbiology_input=micro_input,
            observation=observation,
            icu_round=icu_round
        )
        update_dict = {
            'when': '27/03/2020 09:33:55',
            'initials': 'FJK',
            'infection_control': 'asdf',
            'clinical_discussion': 'asdf',
            'reason_for_interaction': 'ICU round',
            'micro_input_icu_round_relation': {
                'observation': {'temperature': 222},
                'icu_round': {
                    "sofa_score": '12'
                }
            },
            'episode_id': self.episode.id
        }
        micro_input.update_from_dict(update_dict, self.user)
        saved_input = self.episode.microbiologyinput_set.get()
        saved_input.refresh_from_db()
        observation = saved_input.microinputicuroundrelation.observation
        self.assertEqual(
            observation.temperature, 222
        )
        # observatio should gain the datetime
        # of the advice
        self.assertEqual(
            observation.datetime,
            timezone.make_aware(datetime.datetime(
                2020, 3, 27, 9, 33, 55
            ))
        )
        icu_round = saved_input.microinputicuroundrelation.icu_round
        self.assertEqual(
            icu_round.when,
            timezone.make_aware(datetime.datetime(
                2020, 3, 27, 9, 33, 55
            ))
        )
        self.assertEqual(12.0, icu_round.sofa_score)


    def test_update_from_dict_delete_observation(self):
        micro_input = emodels.MicrobiologyInput.objects.create(
            episode=self.episode
        )
        observation =  obs_models.Observation.objects.create(
            episode=self.episode,
            temperature=111,
            datetime=timezone.make_aware(datetime.datetime(
                2020, 3, 26, 10, 33, 55
            ))
        )
        icu_round = emodels.ICURound.objects.create(
            episode=self.episode,
            when=timezone.make_aware(datetime.datetime(
                2020, 3, 26, 10, 33, 55
            )),
            sofa_score='12'
        )
        emodels.MicroInputICURoundRelation.objects.create(
            microbiology_input=micro_input,
            observation=observation,
            icu_round=icu_round
        )

        update_dict = {
            'when': '27/03/2020 09:33:55',
            'initials': 'FJK',
            'infection_control': 'asdf',
            'clinical_discussion': 'asdf',
            'reason_for_interaction': 'Other',
            'micro_input_icu_round_relation': {},
            'episode_id': self.episode.id
        }
        micro_input.update_from_dict(update_dict, self.user)
        saved_input = self.episode.microbiologyinput_set.get()
        saved_input.refresh_from_db()
        self.assertFalse(emodels.MicroInputICURoundRelation.objects.all().exists())
        self.assertFalse(obs_models.Observation.objects.all().exists())
        self.assertFalse(emodels.ICURound.objects.all().exists())

    def test_delete_observation(self):
        micro_input = emodels.MicrobiologyInput.objects.create(
            episode=self.episode
        )
        observation =  obs_models.Observation.objects.create(
            episode=self.episode,
            temperature=111,
            datetime=timezone.make_aware(datetime.datetime(
                2020, 3, 26, 10, 33, 55
            ))
        )
        icu_round = emodels.ICURound.objects.create(
            episode=self.episode,
            when=timezone.make_aware(datetime.datetime(
                2020, 3, 26, 10, 33, 55
            )),
            sofa_score='12'
        )
        emodels.MicroInputICURoundRelation.objects.create(
            microbiology_input=micro_input,
            observation=observation,
            icu_round=icu_round
        )
        observation.delete()
        micro_input.refresh_from_db()
        self.assertIsNone(micro_input.microinputicuroundrelation.observation_id)

    def test_to_dict(self):
        micro_input = emodels.MicrobiologyInput.objects.create(
            episode=self.episode,
            clinical_discussion="some discussion"
        )
        observation =  obs_models.Observation.objects.create(
            episode=self.episode,
            temperature=111,
            datetime=timezone.make_aware(datetime.datetime(
                2020, 3, 26, 10, 33, 55
            ))
        )
        icu_round = emodels.ICURound.objects.create(
            episode=self.episode,
            when=timezone.make_aware(datetime.datetime(
                2020, 3, 26, 10, 33, 55
            )),
            sofa_score='12'
        )
        emodels.MicroInputICURoundRelation.objects.create(
            microbiology_input=micro_input,
            observation=observation,
            icu_round=icu_round
        )
        as_dict = micro_input.to_dict(None)
        self.assertEqual(
            as_dict["clinical_discussion"], "some discussion"
        )

        self.assertEqual(
            as_dict["micro_input_icu_round_relation"]["observation"]["temperature"], 111
        )
        self.assertEqual(
            '12',
            as_dict["micro_input_icu_round_relation"]["icu_round"]["sofa_score"]
        )

    def test_to_dict_for_no_icu_round(self):
        micro_input = emodels.MicrobiologyInput.objects.create(
            episode=self.episode,
            clinical_discussion="some discussion"
        )
        as_dict = micro_input.to_dict(None)
        self.assertEqual(as_dict["micro_input_icu_round_relation"]["observation"], {})
        self.assertEqual(as_dict["micro_input_icu_round_relation"]["icu_round"], {})

    def test_delete_with_icu_round(self):
        micro_input = emodels.MicrobiologyInput.objects.create(
            episode=self.episode,
            clinical_discussion="some discussion"
        )
        observation =  obs_models.Observation.objects.create(
            episode=self.episode,
            temperature=111,
            datetime=timezone.make_aware(datetime.datetime(
                2020, 3, 26, 10, 33, 55
            ))
        )
        icu_round = emodels.ICURound.objects.create(
            episode=self.episode,
            when=timezone.make_aware(datetime.datetime(
                2020, 3, 26, 10, 33, 55
            )),
            sofa_score='12'
        )
        emodels.MicroInputICURoundRelation.objects.create(
            microbiology_input=micro_input,
            observation=observation,
            icu_round=icu_round
        )
        micro_input.delete()
        self.assertFalse(emodels.MicroInputICURoundRelation.objects.all().exists())
        self.assertFalse(obs_models.Observation.objects.all().exists())
        self.assertFalse(emodels.ICURound.objects.all().exists())
        self.assertFalse(emodels.MicrobiologyInput.objects.all().exists())

    def test_delete_without_icu_round(self):
        micro_input = emodels.MicrobiologyInput.objects.create(
            episode=self.episode,
            clinical_discussion="some discussion"
        )
        micro_input.delete()
        self.assertFalse(emodels.MicroInputICURoundRelation.objects.all().exists())
        self.assertFalse(obs_models.Observation.objects.all().exists())
        self.assertFalse(emodels.ICURound.objects.all().exists())
        self.assertFalse(emodels.MicrobiologyInput.objects.all().exists())


class DiagnosisTest(OpalTestCase, AbstractEpisodeTestCase):

    def setUp(self):
        super(DiagnosisTest, self).setUp()
        self.condition_1 = Condition.objects.create(name="Some condition")
        self.condition_2 = Condition.objects.create(name="Some other condition")
        Synonym.objects.create(
            name="Condition synonym",
            content_object=self.condition_2
        )

        self.diagnosis = self.episode.diagnosis_set.create(
            consistency_token="12345678",
            date_of_diagnosis=datetime.date(2013, 7, 25),
            details="",
            provisional=False,
            condition=self.condition_1.name,
        )

        self.episode.diagnosis_set.create(
            condition=self.condition_2.name,
            date_of_diagnosis=datetime.date(2013, 7, 25),
            details="",
            provisional=True,
        )

        self.diagnosis = self.episode.diagnosis_set.first()

    def test_to_dict(self):
        expected_data = {
            'consistency_token': u'12345678',
            'updated': None,
            'created': None,
            'original_mrn': None,
            'category': None,
            'updated_by_id': None,
            'created_by_id': None,
            'episode_id': self.episode.id,
            'id': self.diagnosis.id,
            'condition': 'Some condition',
            'provisional': False,
            'details': u'',
            'date_of_diagnosis': datetime.date(2013, 7, 25),
            }

        result = {str(k): v for k, v in self.diagnosis.to_dict(self.user).items()}
        self.assertEqual(expected_data, result)

    def test_update_from_dict_with_existing_condition(self):
        data = {
            'consistency_token': '12345678',
            'id': self.diagnosis.id,
            'condition': 'Some other condition',
            }
        self.diagnosis.update_from_dict(data, self.user)
        diagnosis = self.episode.diagnosis_set.first()
        self.assertEqual('Some other condition', diagnosis.condition)

    def test_update_from_dict_with_synonym_for_condition(self):
        data = {
            'consistency_token': '12345678',
            'id': self.diagnosis.id,
            'condition': 'Condition synonym',
            }
        self.diagnosis.update_from_dict(data, self.user)
        diagnosis = self.episode.diagnosis_set.first()
        self.assertEqual('Some other condition', diagnosis.condition)

    def test_update_from_dict_with_new_condition(self):
        data = {
            'consistency_token': '12345678',
            'id': self.diagnosis.id,
            'condition': 'New condition',
            }
        self.diagnosis.update_from_dict(data, self.user)
        diagnosis = self.episode.diagnosis_set.first()
        self.assertEqual('New condition', diagnosis.condition)


class ChronicAntifungalTestCase(OpalTestCase):
    def setUp(self):
        self.patient, self.episode = self.new_patient_and_episode_please()
        category_name = episode_categories.InfectionService.display_name
        self.episode.category_name = category_name
        self.episode.save()
        self.now = timezone.now()

    @mock.patch('django.utils.timezone.now')
    def test_includes_new_chronic_antifungal(self, now):
        now.return_value = self.now - datetime.timedelta(3)
        self.patient.chronicantifungal_set.create(
            reason=emodels.ChronicAntifungal.DISPENSARY_REPORT
        )
        self.assertEqual(
            list(emodels.ChronicAntifungal.antifungal_episodes()),
            [self.episode]
        )

    @mock.patch('django.utils.timezone.now')
    def test_includes_multiple_new_chronic_antifungal(self, now):
        now.return_value = self.now - datetime.timedelta(3)
        self.patient.chronicantifungal_set.create(
            reason=emodels.ChronicAntifungal.DISPENSARY_REPORT
        )
        self.patient.chronicantifungal_set.create(
            reason=emodels.ChronicAntifungal.DISPENSARY_REPORT
        )
        self.assertEqual(
            list(emodels.ChronicAntifungal.antifungal_episodes()),
            [self.episode]
        )

    def test_excludes_old_chronic_antifungal(self):

        with mock.patch.object(timezone, 'now') as n:
            n.return_value = self.now - datetime.timedelta(190)
            self.patient.chronicantifungal_set.create(
                reason=emodels.ChronicAntifungal.DISPENSARY_REPORT
            )

        self.assertEqual(
            list(emodels.ChronicAntifungal.antifungal_episodes()), []
        )

    def test_excludes_chrnoic_antifungal_is_none(self):
        self.assertEqual(
            list(emodels.ChronicAntifungal.antifungal_episodes()), []
        )

    def test_ignores_episodes_of_other_categories(self):
        self.episode.category_name = "TB"
        self.episode.save()
        self.patient.chronicantifungal_set.create(
            reason=emodels.ChronicAntifungal.DISPENSARY_REPORT
        )
        self.assertEqual(
            list(emodels.ChronicAntifungal.antifungal_episodes()), []
        )

    def test_signals_with_antifungal_reason(self):
        self.episode.microbiologyinput_set.create(
            reason_for_interaction=emodels.MicrobiologyInput.ANTIFUNGAL_STEWARDSHIP_ROUND
        )
        self.assertTrue(
            self.patient.chronicantifungal_set.filter(
                reason=emodels.ChronicAntifungal.REASON_TO_INTERACTION
            ).exists()
        )

    def test_signals_without_antifungal_reason(self):
        self.episode.microbiologyinput_set.create(
            reason_for_interaction="something"
        )
        self.assertFalse(self.patient.chronicantifungal_set.exists())


class PositiveBloodCultureHistoryTestCase(OpalTestCase):
    def setUp(self):
        self.patient, self.episode = self.new_patient_and_episode_please()

    def test_creation_on_tagging_save(self):
        self.episode.set_tag_names(["bacteraemia"], self.user)
        pbch = self.patient.positivebloodculturehistory_set.get()
        self.assertEqual(pbch.when.date(), datetime.date.today())

    def test_not_created_on_a_different_tag_save(self):
        self.episode.set_tag_names(["something"], self.user)
        self.assertEqual(self.patient.positivebloodculturehistory_set.count(), 0)

    def test_not_updated_on_other_removal(self):
        weeks_ago = timezone.make_aware(datetime.datetime(2017, 1, 1))
        self.episode.set_tag_names(["bacteraemia"], self.user)
        self.patient.positivebloodculturehistory_set.update(
            when=weeks_ago
        )
        self.episode.set_tag_names(["something"], self.user)
        pbch = self.patient.positivebloodculturehistory_set.get()
        self.assertEqual(pbch.when.date(), weeks_ago.date())

    def test_updated_on_repeat_saves(self):
        weeks_ago = timezone.make_aware(datetime.datetime(2017, 1, 1))
        self.episode.set_tag_names(["bacteraemia"], self.user)
        self.patient.positivebloodculturehistory_set.update(
            when=weeks_ago
        )
        self.episode.set_tag_names(["something"], self.user)
        self.episode.set_tag_names(["bacteraemia"], self.user)
        pbch = self.patient.positivebloodculturehistory_set.get()
        self.assertEqual(pbch.when.date(), datetime.date.today())

    def test_only_one_instance_created(self):
        self.episode.set_tag_names(["bacteraemia"], self.user)
        self.episode.set_tag_names(["bacteraemia"], self.user)
        self.assertEqual(self.patient.positivebloodculturehistory_set.count(), 1)

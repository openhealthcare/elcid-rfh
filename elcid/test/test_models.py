import datetime
import ffs
import pytz

from mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.contrib.contenttypes.models import ContentType

from opal.core import exceptions
from opal.core.test import OpalTestCase
from opal.models import (
    Patient, Episode, Condition, Synonym, Symptom, Antimicrobial,
    Microbiology_organism
)
from elcid import models as emodels


HERE = ffs.Path.here()
TEST_DATA = HERE/'test_data'


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
        with self.assertRaises(exceptions.APIError):
            self.demographics.update_from_dict({}, self.user)

    def test_update_from_dict_with_incorrect_consistency_token(self):
        with self.assertRaises(exceptions.ConsistencyError):
            self.demographics.update_from_dict({'consistency_token': '87654321'}, self.user)

    @override_settings(GLOSS_ENABLED=True)
    @patch("opal.models.Subrecord.get_form_template")
    def test_get_demographics_form_with_gloss(self, form_template_mock):
        form_template_mock.return_value = "some_template.html"
        form_template = emodels.Demographics.get_form_template()
        self.assertEqual(form_template, "some_template.html")

    @override_settings(GLOSS_ENABLED=False)
    def test_get_demographics_form_without_gloss(self):
        form_template = emodels.Demographics.get_form_template()
        self.assertEqual(
            form_template, "forms/demographics_form_pre_gloss.html"
        )


class LocationTest(OpalTestCase, AbstractEpisodeTestCase):

    def setUp(self):
        super(LocationTest, self).setUp()

        self.location = emodels.Location.objects.create(
            bed="13",
            category="Inpatient",
            consistency_token="12345678",
            hospital="UCH",
            ward="T10",
            episode=self.episode
        )

    def test_to_dict(self):
        expected_data = {
            'consistency_token': '12345678',
            'episode_id': self.episode.id,
            'id': self.location.id,
            'category': 'Inpatient',
            'hospital': 'UCH',
            'ward': 'T10',
            'bed': '13',
            'created': None,
            'updated': None,
            'updated_by_id': None,
            'created_by_id': None,
            'provenance': '',
            }
        result = {str(k): v for k, v in self.location.to_dict(self.user).iteritems()}
        self.assertEqual(expected_data, result)

    def test_update_from_dict(self):
        data = {
            'consistency_token': '12345678',
            'id': self.location.id,
            'category': 'Inpatient',
            'hospital': 'HH',
            'ward': 'T10',
            'bed': '13',
            }
        self.location.update_from_dict(data, self.user)
        self.assertEqual('HH', self.location.hospital)


class PresentingComplaintTest(OpalTestCase, AbstractEpisodeTestCase):
    def setUp(self):
        super(PresentingComplaintTest, self).setUp()
        self.symptom_1 = Symptom.objects.create(name="tiredness")
        self.symptom_2 = Symptom.objects.create(name="alertness")
        self.symptom_3 = Symptom.objects.create(name="apathy")
        self.presenting_complaint = emodels.PresentingComplaint.objects.create(
            symptom=self.symptom_1,
            duration="a week",
            details="information",
            consistency_token=1111,
            episode=self.episode
        )
        self.presenting_complaint.symptoms.add(self.symptom_2, self.symptom_3)

    def test_to_dict(self):
        expected_data = dict(
            id=self.presenting_complaint.id,
            consistency_token=self.presenting_complaint.consistency_token,
            symptoms=["alertness", "apathy"],
            duration="a week",
            details="information",
            episode_id=1,
            updated=None,
            updated_by_id=None,
            created=None,
            created_by_id=None
        )
        self.assertEqual(
            expected_data, self.presenting_complaint.to_dict(self.user)
        )

    def test_update_from_dict(self):
        data = {
            u'consistency_token': self.presenting_complaint.consistency_token,
            u'id': self.presenting_complaint.id,
            u'symptoms': [u'alertness', u'tiredness'],
            u'duration': 'a month',
            u'details': 'other information'
        }
        self.presenting_complaint.update_from_dict(data, self.user)
        new_symptoms = self.presenting_complaint.symptoms.values_list(
            "name", flat=True
        )
        self.assertEqual(set(new_symptoms), set([u'alertness', u'tiredness']))
        self.assertEqual(self.presenting_complaint.duration, 'a month')
        self.assertEqual(
            self.presenting_complaint.details, 'other information'
        )


class AllergyTest(OpalTestCase):
    def test_get_modal_footer_template(self):
        self.assertEqual(
            emodels.Allergies.get_modal_footer_template(),
            "partials/_sourced_modal_footer.html"
        )

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


class BloodCultureMixinTestCase(OpalTestCase):
    def test_subclassed(self):
        blood_culture_tests = [
            emodels.GramStain,
            emodels.QuickFISH,
            emodels.GPCStaph,
            emodels.GPCStrep,
            emodels.GNR,
            emodels.BloodCultureOrganism
        ]

        for model in blood_culture_tests:
            self.assertTrue(
                issubclass(model, emodels.BloodCultureMixin)
            )

    def test_get_record(self):
        self.assertEqual(
            emodels.BloodCultureMixin.get_record(),
            "lab/records/blood_culture.html"
        )

    def test_update_from_dict_with_no_result_observation(self):
        patient, _ = self.new_patient_and_episode_please()
        gram_stain = emodels.GramStain.objects.create(patient=patient)
        gram_stain.update_from_dict(dict(
            lab_test_type=emodels.GramStain.get_display_name(),
            result=None
        ))
        self.assertEqual(emodels.GramStain.objects.count(), 0)

    def test_update_from_dict_with_empty_result_observation(self):
        patient, _ = self.new_patient_and_episode_please()
        gram_stain = emodels.GramStain.objects.create(patient=patient)
        gram_stain.update_from_dict(dict(
            lab_test_type=emodels.GramStain.get_display_name(),
            result=None
        ))
        self.assertEqual(emodels.GramStain.objects.count(), 0)

    def test_update_from_dict_with_not_done(self):
        patient, _ = self.new_patient_and_episode_please()
        gram_stain = emodels.GramStain.objects.create(patient=patient)
        gram_stain.update_from_dict(dict(
            lab_test_type=emodels.GramStain.get_display_name(),
            result=dict(result="Not Done")
        ))
        self.assertEqual(emodels.GramStain.objects.count(), 0)

    def test_update_from_dict_with_not_done_with_a_new_model(self):
        patient, _ = self.new_patient_and_episode_please()
        gram_stain = emodels.GramStain(patient=patient)
        gram_stain.update_from_dict(dict(
            lab_test_type=emodels.GramStain.get_display_name(),
            result=dict(result="Not Done")
        ))
        self.assertEqual(emodels.GramStain.objects.count(), 0)

    def test_update_from_dict_with_valid_result(self):
        patient, _ = self.new_patient_and_episode_please()
        gram_stain = emodels.GramStain(patient=patient)
        gram_stain.update_from_dict(dict(
            lab_test_type=emodels.GramStain.get_display_name(),
            result=dict(result="Yeast")
        ), self.user)
        self.assertEqual(emodels.GramStain.objects.count(), 1)


class RfhObservationMixinTestCase(OpalTestCase):
    def test_to_unicode(self):
        patient, _ = self.new_patient_and_episode_please()
        gram_stain = emodels.GramStain(patient=patient)
        gram_stain.update_from_dict(dict(
            lab_test_type=emodels.GramStain.get_display_name(),
            result=dict(result="Yeast")
        ), self.user)
        self.assertEqual(gram_stain.observations.count(), 1)
        observation = gram_stain.observations.get()
        self.assertTrue(
            observation.__unicode__().startswith(
                "GramStainResult for gram_stain: 1"
            )
        )


class HL7ResultTestCase(OpalTestCase, AbstractEpisodeTestCase):
    def test_update_from_dict_repeated(self):
        emodels.HL7Result.objects.create(
            patient=self.patient,
            external_identifier="1",
            status=emodels.HL7Result.PENDING
        )
        update_dict = dict(
            external_identifier="1",
            status=emodels.HL7Result.COMPLETE
        )
        hl7_result = emodels.HL7Result(patient_id=self.patient.id)
        hl7_result.update_from_dict(update_dict, self. user)

        found_hl7_result = emodels.HL7Result.objects.get()
        self.assertEqual(found_hl7_result.status, emodels.HL7Result.COMPLETE)

    def test_update_from_dict_first_time(self):
        update_dict = dict(
            external_identifier="1",
            status=emodels.HL7Result.COMPLETE
        )
        hl7_result = emodels.HL7Result(patient_id=self.patient.id)
        hl7_result.update_from_dict(update_dict, self. user)

        found_hl7_result = emodels.HL7Result.objects.get()
        self.assertEqual(found_hl7_result.status, emodels.HL7Result.COMPLETE)

    def test_error_raised_if_external_identifier_not_in_dict(self):
        update_dict = dict(
            status=emodels.HL7Result.COMPLETE
        )
        hl7_result = emodels.HL7Result(patient_id=self.patient.id)

        with self.assertRaises(ValueError) as e:
            hl7_result.update_from_dict(update_dict, self. user)

        self.assertEqual(
            str(e.exception),
            "an external identifier is required in {'status': 'complete'}"
        )


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
            'updated_by_id': None,
            'created_by_id': None,
            'episode_id': self.episode.id,
            'id': self.diagnosis.id,
            'condition': 'Some condition',
            'provisional': False,
            'details': u'',
            'date_of_diagnosis': datetime.date(2013, 7, 25),
            }

        result = {str(k): v for k, v in self.diagnosis.to_dict(self.user).iteritems()}
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
        weeks_ago = datetime.datetime(2017, 1, 1)
        self.episode.set_tag_names(["bacteraemia"], self.user)
        self.patient.positivebloodculturehistory_set.update(
            when=weeks_ago
        )
        self.episode.set_tag_names(["something"], self.user)
        pbch = self.patient.positivebloodculturehistory_set.get()
        self.assertEqual(pbch.when.date(), weeks_ago.date())

    def test_updated_on_repeat_saves(self):
        weeks_ago = datetime.datetime(2017, 1, 1)
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

import datetime
import ffs
import pytz
from django.conf import settings
from django.test import TestCase

from opal.core import exceptions
from opal.core.test import OpalTestCase
from opal.models import Patient, Episode, Condition, Synonym
from elcid.models import Location, Result

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
            'middle_name': '',
            'title_fk_id': None,
            'title_ft': u'',
            'title': '',
            'marital_status_fk_id': None,
            'marital_status_ft': u'',
            'marital_status': u'',
            'religion': '',
            'created': None,
            'updated': None,
            'created_by_id': None,
            'updated_by_id': None,
            'date_of_birth': datetime.date(1972, 6, 20),
            'birth_place': '',
            'birth_place_fk_id': None,
            'birth_place_ft': '',
            'ethnicity_fk_id': None,
            'ethnicity_ft': u'',
            'ethnicity': u'',
            'sex_fk_id': None,
            'sex_ft': '',
            'sex': '',
            'hospital_number': 'AA1111',
            'nhs_number': None,
            'date_of_death': None,
            'post_code': '',
            'gp_practice_code': '',
            'sourced_from_upstream': False,
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


class LocationTest(OpalTestCase, AbstractEpisodeTestCase):

    def setUp(self):
        super(LocationTest, self).setUp()

        self.location = Location.objects.create(
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
            'category_fk_id': None,
            'category_ft': 'Inpatient',
            'hospital': 'UCH',
            'ward': 'T10',
            'bed': '13',
            'created': None,
            'updated': None,
            'updated_by_id': None,
            'created_by_id': None,
            'provenance': '',
            'provenance_fk_id': None,
            'provenance_ft': '',
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


class ResultTest(OpalTestCase, AbstractEpisodeTestCase):
    def test_to_dict_and_from_dict(self):
        datetime_format = settings.DATETIME_INPUT_FORMATS[0]

        request_datetime = datetime.datetime(2016, 1, 2).strftime(
            datetime_format
        )
        observation_datetime = datetime.datetime(2016, 1, 6).strftime(
            datetime_format
        )
        last_edited = datetime.datetime(2016, 1, 7).strftime(
            datetime_format
        )

        result_args = dict(
            episode_id=self.episode.id,
            lab_number="234324",
            profile_code="2343344",
            profile_description="RENAL PROFILE",
            request_datetime=request_datetime,
            observation_datetime=observation_datetime,
            last_edited=last_edited,
            result_status="FINAL",
            observations=[{
                u'comments': None,
                u'observation_value': u'250',
                u'reference_range': u'150-400',
                u'result_status': None,
                u'test_code': u'PLT',
                u'test_name': u'Platelet count',
                u'units': u'x10^9/L',
                u'value_type': u'NM'
            }, {
                u'comments': None,
                u'observation_value': u'10.0',
                u'reference_range': u'7-13',
                u'result_status': None,
                u'test_code': u'MPVU',
                u'test_name': u'MPV',
                u'units': u'fL',
                u'value_type': u'NM'
            }]
        )

        result = Result()
        result.update_from_dict(result_args, self.user)

        found_result = Result.objects.get()
        self.assertEqual(found_result.lab_number, "234324")
        self.assertEqual(found_result.profile_code, "2343344")

        back_to_dict = found_result.to_dict(self.user)
        del back_to_dict["updated"]
        del back_to_dict["updated_by_id"]
        del back_to_dict["created"]
        del back_to_dict["created_by_id"]
        del back_to_dict["consistency_token"]
        del back_to_dict["id"]
        result_args["request_datetime"] = datetime.datetime(
            2016, 1, 2, tzinfo=pytz.UTC
        )
        result_args["observation_datetime"] = datetime.datetime(
            2016, 1, 6, tzinfo=pytz.UTC
        )
        result_args["last_edited"] = datetime.datetime(
            2016, 1, 7, tzinfo=pytz.UTC
        )

        self.assertEqual(result_args, back_to_dict)


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
            'condition_fk_id': self.condition_1.id,
            'condition_ft': u'',
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

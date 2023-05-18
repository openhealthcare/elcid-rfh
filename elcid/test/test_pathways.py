from datetime import date
from unittest.mock import patch
from django.test import override_settings
from django.contrib.auth.models import User

from opal import models
from opal.core.test import OpalTestCase
from intrahospital_api import constants
from elcid.pathways import (
    AddPatientPathway, IgnoreDemographicsMixin
)
from elcid import models as emodels
from intrahospital_api import update_demographics


@override_settings(
    ASYNC_API=False,
    INTRAHOSPITAL_API='intrahospital_api.apis.dev_api.DevApi',
    API_USER="ohc"
)
class PathwayTestCase(OpalTestCase):
    def setUp(self):
        super(PathwayTestCase, self).setUp()
        User.objects.create(username="ohc", password="fake_password")


class IgnoreDemographicsMixinTestCase(PathwayTestCase):
    def setUp(self):
        class SomeSaveParentPathway(object):
            def save(self, data, user=None, episode=None, patient=None):
                self.data = data
                self.user = user
                self.episode = episode
                self.patient = patient

        class SomeSaveChildPathway(
            IgnoreDemographicsMixin, SomeSaveParentPathway
        ):
            pass

        self.pathway = SomeSaveChildPathway()
        self.patient, self.episode = self.new_patient_and_episode_please()

    def test_popped_with_external_system(self):
        self.patient.demographics_set.update(
            first_name="Paul",
            surname="Daniels",
            external_system=constants.EXTERNAL_SYSTEM
        )
        data = dict(demographics=[{"first_name": "Daniel"}])
        self.pathway.save(
            data, user=self.user, episode=self.episode, patient=self.patient
        )

        self.assertEqual(
            self.pathway.user, self.user
        )
        self.assertEqual(
            self.pathway.episode, self.episode
        )
        self.assertEqual(
            self.pathway.patient, self.patient
        )
        self.assertEqual(
            self.pathway.data, {}
        )

    def test_popped_without_external_system(self):
        self.patient.demographics_set.update(
            first_name="Paul",
            surname="Daniels",
        )
        data = dict(demographics=[{"first_name": "Daniel"}])
        self.pathway.save(
            data, user=self.user, episode=self.episode, patient=self.patient
        )

        self.assertEqual(
            self.pathway.user, self.user
        )
        self.assertEqual(
            self.pathway.episode, self.episode
        )
        self.assertEqual(
            self.pathway.patient, self.patient
        )
        self.assertEqual(
            self.pathway.data, dict(demographics=[{"first_name": "Daniel"}])
        )


def create_patient(mrn, episode_category):
    patient = models.Patient.objects.create()
    patient.demographics_set.update(hospital_number=mrn)
    patient.episode_set.create(category_name=episode_category.display_name)
    return patient, True


@patch('elcid.pathways.loader.get_or_create_patient')
class TestAddPatientPathway(OpalTestCase):
    def setUp(self):
        super(TestAddPatientPathway, self).setUp()
        self.assertTrue(
            self.client.login(
                username=self.user.username, password=self.PASSWORD
            )
        )
        self.url = AddPatientPathway().save_url()

    def test_creates_patients_in_the_generic_case(self, create_rfh_patient_from_hospital_number):
        create_rfh_patient_from_hospital_number.side_effect = create_patient
        test_data = dict(
            demographics=[dict(hospital_number="234", nhs_number="12312")],
            location=[dict(ward="9W", hospital="RFH")]
        )
        self.post_json(self.url, test_data)
        patient = models.Patient.objects.get()
        self.assertEqual(
            patient.demographics_set.first().hospital_number,
            "234"
        )

    def test_does_not_error_if_hospital_is_not_set(self, create_rfh_patient_from_hospital_number):
        """
        Hospital will not be populated for new patients where the
        user enters nothing in the location form's hospital field.

        We should not error.
        """
        create_rfh_patient_from_hospital_number.side_effect = create_patient
        test_data = dict(
            demographics=[dict(hospital_number="234", nhs_number="12312")],
            location=[dict(ward="9W")]
        )
        self.post_json(self.url, test_data)
        patient = models.Patient.objects.get()
        self.assertEqual(
            patient.demographics_set.first().hospital_number,
            "234"
        )

    def test_does_not_error_if_location_is_not_set(self, create_rfh_patient_from_hospital_number):
        """
        Location will not be populated for new patients where the
        user enters nothing in the location form.

        We should not error.
        """
        create_rfh_patient_from_hospital_number.side_effect = create_patient
        test_data = dict(
            demographics=[dict(hospital_number="234", nhs_number="12312")],
        )
        self.post_json(self.url, test_data)
        patient = models.Patient.objects.get()
        self.assertEqual(
            patient.demographics_set.first().hospital_number,
            "234"
        )
        episode = patient.episode_set.get()
        self.assertEqual(
            list(episode.get_tag_names(None)),
            []
        )

    def test_create_new_patient_with_stripped_zeros(self, create_rfh_patient_from_hospital_number):
        """
        We should strip leading zeros from hospital numbers before creating
        patients.
        """
        create_rfh_patient_from_hospital_number.side_effect = create_patient
        url = AddPatientPathway().save_url()
        test_data = dict(
            demographics=[dict(hospital_number="00234", nhs_number="12312")],
        )
        self.post_json(url, test_data)
        self.assertTrue(
            emodels.Demographics.objects.filter(hospital_number="234").exists()
        )

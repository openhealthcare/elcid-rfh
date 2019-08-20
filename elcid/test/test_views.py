"""
Unittests for the UCLH eLCID OPAL implementation.
"""
import datetime
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import ffs

from opal.core.test import OpalTestCase
from opal.models import Patient
from opal.core.subrecords import subrecords

from elcid import views


HERE = ffs.Path.here()
TEST_DATA = HERE/'test_data'


class ViewsTest(OpalTestCase):
    fixtures = ['patients_users', 'patients_options', 'patients_records']

    def setUp(self):
        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.PASSWORD))
        self.patient = Patient.objects.get(pk=1)

    def test_try_to_update_nonexistent_demographics_subrecord(self):
        response = self.put_json('/api/v0.1/demographics/1234/', {})
        self.assertEqual(404, response.status_code)

    def test_episode_list_template_view(self):
        self.assertStatusCode('/templates/patient_list.html/team_1', 200)

    def test_episode_detail_template_view(self):
        self.assertStatusCode('/templates/episode_detail.html/1', 200)

    def test_add_patient_template_view(self):
        self.assertStatusCode('/templates/modals/add_episode.html/', 200)

    def test_delete_item_confirmation_template_view(self):
        self.assertStatusCode('/templates/delete_item_confirmation_modal.html/', 200)

    def test_all_modal_templates(self):
        """ This renders all of our modal templates and blows up
            if they fail to render
        """
        for i in subrecords():
            if i.get_form_template():
                url = reverse("{}_modal".format(i.get_api_name()))
                self.assertStatusCode(url, 200)


class DetailSchemaViewTest(OpalTestCase):
    fixtures = ['patients_users', 'patients_options', 'patients_records']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.assertTrue(self.client.login(username=self.user.username,
                                          password='password'))
        self.patient = Patient.objects.get(pk=1)
        schema_file = TEST_DATA/'detail.schema.json'
        self.schema = schema_file.json_load()

    def assertStatusCode(self, path, expected_status_code):
        response = self.client.get(path)
        self.assertEqual(expected_status_code, response.status_code)


class ExtractSchemaViewTest(OpalTestCase):
    fixtures = ['patients_users', 'patients_options', 'patients_records']

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.assertTrue(self.client.login(username=self.user.username,
                                          password='password'))
        self.patient = Patient.objects.get(pk=1)
        schema_file = TEST_DATA/'extract.schema.json'
        self.schema = schema_file.json_load()

    def assertStatusCode(self, path, expected_status_code):
        response = self.client.get(path)
        self.assertEqual(expected_status_code, response.status_code)


class WardSortTestCase(OpalTestCase):
    def test_ward_sort(self):
        wards = [
            "8 West",
            "PITU",
            "ICU 4 East",
            "9 East",
            "8 South",
            "Other",
            "9 North",
            "ICU 4 West",
            "12 West",
            "Outpatients",
        ]

        expected = [
            "8 South",
            "8 West",
            "9 East",
            "9 North",
            "12 West",
            "ICU 4 East",
            "ICU 4 West",
            "Outpatients",
            "PITU",
            "Other"
        ]
        self.assertEqual(
            expected, sorted(wards, key=views.ward_sort_key)
        )

    def test_grouping(self):
        wards = [
            "8 West",
            "8 West",
            "9 East",
            "8 South",
            "9 North",
        ]

        expected = [
            "8 South",
            "8 West",
            "8 West",
            "9 East",
            "9 North",
        ]
        self.assertEqual(
            expected, sorted(wards, key=views.ward_sort_key)
        )


class RenalHandoverTestCase(OpalTestCase):
    def test_vanilla(self):
        patient_1, episode_1 = self.new_patient_and_episode_please()
        episode_1.set_tag_names(["renal"], None)
        patient_1.demographics_set.update(
            first_name="Wilma",
            surname="Flintstone",
            hospital_number="123"
        )
        location = episode_1.location_set.get()
        location.ward = "10 East"
        location.bed = "1"
        location.save()
        microinput = episode_1.microbiologyinput_set.create(
            clinical_discussion=["some_discussion"]
        )
        diagnosis = episode_1.diagnosis_set.create()
        diagnosis.condition = "Cough"
        diagnosis.save()

        primary_diagnosis = episode_1.primarydiagnosis_set.get()
        primary_diagnosis.condition = "Fever"
        primary_diagnosis.save()

        line = episode_1.line_set.create()
        line.line_type = "Hickman"
        line.save()

        bcs = episode_1.patient.bloodcultureset_set.create(lab_number="123")

        ctx = views.RenalHandover().get_context_data()
        episode = ctx["ward_and_episodes"][0]["episodes"][0]
        episode['clinical_advices'] = list(episode['clinical_advices'])
        episode['lines'] = list(episode['lines'])
        episode['blood_culture_sets'] = list(episode['blood_culture_sets'])

        self.assertEqual(
            ctx["ward_and_episodes"][0]["ward"], "10 East"
        )

        self.assertEqual(
            ctx["ward_and_episodes"][0]["episodes"], [{
                'name': 'Wilma Flintstone',
                'hospital_number': '123',
                'diagnosis': 'Cough',
                'clinical_advices': [microinput],
                'unit_ward': '10 East/1',
                'primary_diagnosis': 'Fever',
                'lines': [line],
                "blood_culture_sets": [bcs]
            }]
        )

    def test_aggregate_by_ward(self):
        patient_1, episode_1 = self.new_patient_and_episode_please()
        patient_1.demographics_set.update(
            first_name="Wilma",
            surname="Flintstone"
        )
        patient_2, episode_2 = self.new_patient_and_episode_please()
        patient_2.demographics_set.update(
            first_name="Betty",
            surname="Rubble"
        )
        episode_1.set_tag_names(["renal"], None)
        episode_2.set_tag_names(["renal"], None)

        location_1 = episode_1.location_set.get()
        location_1.ward = "10 East"
        location_1.bed = "1"
        location_1.save()
        location_2 = episode_2.location_set.get()
        location_2.ward = "10 East"
        location_2.bed = "2"
        location_2.save()
        ctx = views.RenalHandover().get_context_data()
        result = ctx["ward_and_episodes"][0]
        self.assertEqual(
            result["ward"], "10 East"
        )
        self.assertEqual(
            len(result["episodes"]), 2
        )

    def test_split_by_ward(self):
        patient_1, episode_1 = self.new_patient_and_episode_please()
        patient_1.demographics_set.update(
            first_name="Wilma",
            surname="Flintstone"
        )
        patient_2, episode_2 = self.new_patient_and_episode_please()
        patient_2.demographics_set.update(
            first_name="Betty",
            surname="Rubble"
        )
        episode_1.set_tag_names(["renal"], None)
        episode_2.set_tag_names(["renal"], None)

        location_1 = episode_1.location_set.get()
        location_1.ward = "10 East"
        location_1.bed = "1"
        location_1.save()
        location_2 = episode_2.location_set.get()
        location_2.ward = "10 West"
        location_2.bed = "2"
        location_2.save()
        ctx = views.RenalHandover().get_context_data()
        east_10 = ctx["ward_and_episodes"][0]
        self.assertEqual(
            east_10["ward"], "10 East"
        )
        self.assertEqual(
            len(east_10["episodes"]), 1
        )
        west_10 = ctx["ward_and_episodes"][1]
        self.assertEqual(
            west_10["ward"], "10 West"
        )
        self.assertEqual(
            len(west_10["episodes"]), 1
        )

    def test_aggregate_clinical_advice(self):
        patient, episode_1 = self.new_patient_and_episode_please()

        episode_2 = patient.episode_set.create()
        episode_3 = patient.episode_set.create()

        location = episode_2.location_set.get()
        location.ward = "10 East"
        location.bed = "1"
        location.save()

        episode_2.set_tag_names(["renal"], None)

        first = timezone.now() - datetime.timedelta(4)
        second = timezone.now() - datetime.timedelta(2)
        third = timezone.now() - datetime.timedelta(1)

        episode_1.microbiologyinput_set.create(
            clinical_discussion="second",
            when=second
        )

        episode_2.microbiologyinput_set.create(
            clinical_discussion="first",
            when=first
        )

        episode_3.microbiologyinput_set.create(
            clinical_discussion="third",
            when=third
        )

        ctx = views.RenalHandover().get_context_data()

        self.assertEqual(
            len(ctx["ward_and_episodes"]), 1
        )

        self.assertEqual(
            len(ctx["ward_and_episodes"][0]["episodes"]), 1
        )
        micro_inputs = ctx["ward_and_episodes"][0]["episodes"][0][
            "clinical_advices"
        ]
        discussion = list(micro_inputs.values_list(
            "clinical_discussion", flat=True
        ))
        self.assertEqual(
            discussion, ["first", "second", "third"]
        )

    def test_other(self):
        # if the patient has no ward we should just put them in `other`
        patient_1, episode_1 = self.new_patient_and_episode_please()
        patient_1.demographics_set.update(
            first_name="Wilma",
            surname="Flintstone"
        )
        episode_1.set_tag_names(["renal"], None)

        location_1 = episode_1.location_set.get()
        location_1.bed = "1"
        location_1.save()
        ctx = views.RenalHandover().get_context_data()
        self.assertEqual(ctx["ward_and_episodes"][0]["ward"], "Other")
        self.assertEqual(len(ctx["ward_and_episodes"][0]["episodes"]), 1)

    def test_single_patient_with_multiple_episodes(self):
        # if the patient has multiple renal episodes we should just use
        # the most recent
        # if the patient has no ward we should just put them in `other`
        patient_1, episode_1 = self.new_patient_and_episode_please()
        episode_1.start = timezone.now() - datetime.timedelta(2)
        episode_2 = patient_1.episode_set.create(
            start=timezone.now() - datetime.timedelta(1)
        )

        primary_diagnosis = episode_1.primarydiagnosis_set.get()
        primary_diagnosis.condition = "Should not appear"
        primary_diagnosis.save()

        primary_diagnosis = episode_2.primarydiagnosis_set.get()
        primary_diagnosis.condition = "Should appear"
        primary_diagnosis.save()

        episode_1.set_tag_names(["renal"], None)
        episode_2.set_tag_names(["renal"], None)

        ctx = views.RenalHandover().get_context_data()
        self.assertEqual(len(ctx["ward_and_episodes"][0]["episodes"]), 1)

        self.assertEqual(len(ctx["ward_and_episodes"]), 1)
        self.assertEqual(ctx["ward_and_episodes"][0]["ward"], "Other")
        self.assertEqual(len(ctx["ward_and_episodes"][0]["episodes"]), 1)
        self.assertEqual(
            ctx["ward_and_episodes"][0]["episodes"][0]["primary_diagnosis"],
            "Should appear"
        )

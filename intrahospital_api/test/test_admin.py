import mock
from django.contrib.admin.sites import AdminSite
from opal.core.test import OpalTestCase
from opal import models as omodels
from intrahospital_api import admin


class TaggingListFilterTestCase(OpalTestCase):
    def setUp(self):
        self.request = mock.MagicMock()
        self.model_admin = mock.MagicMock()
        params = dict()
        model = mock.MagicMock()
        self.tagging_list_filter = admin.TaggingListFilter(
            self.request, params, model, self.model_admin
        )
        self.patient_1, episode_1 = self.new_patient_and_episode_please()
        self.patient_2, episode_2 = self.new_patient_and_episode_please()
        self.patient_3, episode_3 = self.new_patient_and_episode_please()
        self.patient_4, episode_4 = self.new_patient_and_episode_please()
        episode_5 = self.patient_4.create_episode()
        episode_1.set_tag_names(['bacteraemia'], self.user)
        episode_1.set_tag_names([], self.user)
        episode_2.set_tag_names(['bacteraemia'], self.user)
        episode_3.set_tag_names(['icu'], self.user)

        # make sure that a patient with 2 different episodes on the
        # same list does not appear twice
        episode_4.set_tag_names(['icu'], self.user)
        episode_5.set_tag_names(['icu'], self.user)

    def test_lookups(self):
        lookups = self.tagging_list_filter.lookups(
            self.request, self.model_admin
        )

        expected = [
            ('bacteraemia-current', 'bacteraemia - current',),
            ('bacteraemia-previously', 'bacteraemia - previously',),
            ('icu-current', 'icu - current',),
            ('icu-previously', 'icu - previously',),
        ]

        self.assertEqual(
            lookups, expected
        )

    def test_admin_queryset_none(self):
        with mock.patch.object(self.tagging_list_filter, "value") as v:
            v.return_value = None
            qs = self.tagging_list_filter.queryset(self.request, None)
        self.assertEqual(
            set(qs), set(omodels.Patient.objects.all())
        )

    def test_admin_queryset_current(self):
        with mock.patch.object(self.tagging_list_filter, "value") as v:
            v.return_value = "icu-current"
            qs = self.tagging_list_filter.queryset(self.request, None)
        self.assertEqual(
            set(qs), set([self.patient_3, self.patient_4])
        )

    def test_admin_queryset_previously(self):
        with mock.patch.object(self.tagging_list_filter, "value") as v:
            v.return_value = "bacteraemia-previously"
            qs = self.tagging_list_filter.queryset(self.request, None)
        self.assertEqual(
            set(qs), set([self.patient_1])
        )


class PatientAdminTestCase(OpalTestCase):
    def setUp(self):
        self.patient, self.episode = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(hospital_number="123")
        self.site = AdminSite()
        self.admin = admin.PatientAdmin(omodels.Patient, self.site)

    def test_upstream_lab_results(self):
        r = "<a href='/intrahospital_api/raw/results/123'>/intrahospital_api/\
raw/results/123</a>"
        self.assertEqual(self.admin.upstream_lab_results(self.patient), r)

    def test_upstream_blood_culture_results(self):
        r = "<a href='/intrahospital_api/raw/results/123/test/BLOOD%20CULTURE'\
>/intrahospital_api/raw/results/123/test/BLOOD%20CULTURE</a>"
        self.assertEqual(
            self.admin.upstream_blood_culture_results(self.patient),
            r
        )

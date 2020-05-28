"""
Unittests for icu.loader
"""
import datetime
from unittest import mock

from opal.core.test import OpalTestCase
from opal.models import Patient

from plugins.icu import loader, models


@mock.patch('plugins.icu.loader.get_upstream_data')
class LoadICUHandoverTestCase(OpalTestCase):

    def setUp(self):
        p, e = self.new_patient_and_episode_please()
        self.patient = p
        self.demographics = self.patient.demographics()
        self.demographics.hospital_number = 'F-555'
        self.demographics.save()

    def test_creates_new_patient(self, upstream):
        upstream.return_value = [{
            'Patient_MRN'       : '12345678',
            'Date_ITU_Admission': datetime.datetime.now(),
            'Location'          : 'ICU4_West_Bed-12',
        }]

        with mock.patch.object(loader, 'create_rfh_patient_from_hospital_number') as mock_create:

            def create(mrn, service):
                patient      = Patient.objects.create()
                demographics = patient.demographics()
                demographics.hospital_number = mrn
                demographics.save()


            mock_create.side_effect = create

            loader.load_icu_handover()
            mock_create.assert_called_with('12345678', loader.InfectionService)


    def test_new_handover(self, upstream):

        upstream.return_value = [{
            'Patient_MRN'       : 'F-555',
            'Date_ITU_Admission': datetime.datetime.now(),
            'Location'          : 'ICU4_South_Bed-15',
        }]

        loader.load_icu_handover()

        handover = models.ICUHandover.objects.get(patient=self.patient)
        self.assertEqual('ICU4_South_Bed-15', handover.location)


    def test_new_handover_location(self, upstream):
        upstream.return_value = [{
            'Patient_MRN'       : 'F-555',
            'Date_ITU_Admission': datetime.datetime.now(),
            'Location'          : 'ICU4_South_Bed-15',
        }]

        loader.load_icu_handover()

        handover_location = models.ICUHandoverLocation.objects.get(patient=self.patient)
        self.assertEqual('15', handover_location.bed)


    def test_only_one_handover_location(self, upstream):
        p, e = self.new_patient_and_episode_please()
        demographics = p.demographics()
        demographics.hospital_number = 'F-556'
        demographics.save()

        upstream.return_value = [{
            'Patient_MRN'       : 'F-555',
            'Date_ITU_Admission': datetime.datetime.now(),
            'Location'          : 'ICU4_South_Bed-15',
        }]

        loader.load_icu_handover()
        upstream.return_value = [{
            'Patient_MRN'       : 'F-556',
            'Date_ITU_Admission': datetime.datetime.now(),
            'Location'          : 'ICU4_South_Bed-15',
        }]
        loader.load_icu_handover()

        self.assertEqual(1, models.ICUHandoverLocation.objects.count())

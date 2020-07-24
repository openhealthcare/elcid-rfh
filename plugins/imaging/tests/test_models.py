from django.utils import timezone
from opal.core.test import OpalTestCase
from plugins.imaging import models


class ImagingTestCase(OpalTestCase):
    def setUp(self):
        patient, _ = self.new_patient_and_episode_please()
        now = timezone.now()
        self.imaging = models.Imaging.objects.create(
            patient=patient,
            sql_id="1",
            patient_number="123",
            patient_surname="Doe",
            patient_forename="Jane",
            result_id="234",
            order_number="345",
            order_effective_date=now,
            date_of_result=now,
            date_reported=now,
            requesting_user_code="R2D2",
            requesting_user_name="Anakin",
            cerner_visit_id="235d",
            result_code="987s",
            result_description="some description",
            result_status="some status",
            obx_result="some result"
        )

    def test_to_dict_fields(self):
        as_dict = self.imaging.to_dict()
        for field in models.Imaging.FIELDS_TO_SERIALIZE:
            self.assertIn(field, as_dict)

    def test_reported_by_split(self):
        r = "Some information\nReported By: Anne Investigator"
        self.imaging.obx_result = r
        as_dict = self.imaging.to_dict()
        self.assertEqual(
            as_dict["obx_result"], "Some information\n"
        )

    def test_obx_result_none(self):
        self.imaging.obx_result = None
        as_dict = self.imaging.to_dict()
        self.assertEqual(as_dict["obx_result"], "")

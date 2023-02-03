import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from opal.core.test import OpalTestCase
from plugins.admissions import detail, views
from plugins.ipc import constants as ipc_constants


class LocationHistoryViewVisibilityTestCase(OpalTestCase):
    def setUp(self):
        self.view_user = User.objects.create(
            username="view_user"
        )

    def test_superuser(self):
        self.view_user.is_superuser = True
        self.assertTrue(detail.LocationHistoryView.visible_to(
            self.view_user
        ))

    def test_ipc(self):
        self.view_user.profile.roles.create(
            name=ipc_constants.IPC_ROLE
        )
        self.assertTrue(detail.LocationHistoryView.visible_to(
            self.view_user
        ))

    def test_other_user(self):
        self.assertFalse(detail.LocationHistoryView.visible_to(
            self.view_user
        ))


class LocationHistoryEncounterContactsViewTestCase(OpalTestCase):
    """
    There are 6 tests thart we are doing in when looking for overlapping
    hospital stays.
    """
    def setUp(self):
        # initialise the user
        self.user
        self.patient, _ = self.new_patient_and_episode_please()
        self.patient.demographics_set.update(
            hospital_number="123"
        )
        self.other_patient, _ = self.new_patient_and_episode_please()
        self.other_patient.demographics_set.update(
            hospital_number="234"
        )
        self.transfer_history = self.patient.transferhistory_set.create(
            encounter_id="1",
            mrn="123",
            transfer_start_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 10),
            ),
            transfer_end_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 15),
            ),
        )
        self.url = reverse(
            'location_history_encounter_contacts',
            kwargs={"encounter_id": "1"}
        )
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def tests_overlapping_start_date(self):
        """
        We should include a transfer is an overlaps
        the encounter transfers start date.
        """
        th = self.other_patient.transferhistory_set.create(
            transfer_start_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 9),
            ),
            transfer_end_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 11),
            ),
        )
        ctx = self.client.get(self.url).context_data
        transfer = ctx["slices"][0]
        self.assertEqual(
            transfer.contact_transfers[0].id, th.id
        )

    def tests_overlapping_end_date(self):
        """
        We should include a transfer is an overlaps
        the encounter transfers end date.
        """
        th = self.other_patient.transferhistory_set.create(
            transfer_start_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 11),
            ),
            transfer_end_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 16),
            ),
        )
        ctx = self.client.get(self.url).context_data
        transfer = ctx["slices"][0]
        self.assertEqual(
            transfer.contact_transfers[0].id, th.id
        )

    def tests_transfer_within_the_transfer(self):
        """
        We should include a transfer begins and ends within
        the encounter transfer
        """
        th = self.other_patient.transferhistory_set.create(
            transfer_start_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 11),
            ),
            transfer_end_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 14),
            ),
        )
        ctx = self.client.get(self.url).context_data
        transfer = ctx["slices"][0]
        self.assertEqual(
            transfer.contact_transfers[0].id, th.id
        )

    def tests_transfer_ecompasses_the_transfer(self):
        """
        We should include a transfer begins before the
        encounter transfer and ends after the encounter transfer
        """
        th = self.other_patient.transferhistory_set.create(
            transfer_start_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 3),
            ),
            transfer_end_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 24),
            ),
        )
        ctx = self.client.get(self.url).context_data
        transfer = ctx["slices"][0]
        self.assertEqual(
            transfer.contact_transfers[0].id, th.id
        )

    def tests_ignores_transfers_before(self):
        """
        We should not include transfers that
        begin and end before the encoutner transfer
        """
        self.other_patient.transferhistory_set.create(
            transfer_start_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 3),
            ),
            transfer_end_datetime=timezone.make_aware(
                datetime.datetime(2023, 1, 4),
            ),
        )
        ctx = self.client.get(self.url).context_data
        transfer = ctx["slices"][0]
        self.assertEqual(
            len(transfer.contact_transfers), 0
        )

    def tests_ignores_transfers_end(self):
        """
        We should not include transfers that
        begin and end after the encoutner transfer
        """
        self.other_patient.transferhistory_set.create(
            transfer_start_datetime=timezone.make_aware(
                datetime.datetime(2023, 2, 3),
            ),
            transfer_end_datetime=timezone.make_aware(
                datetime.datetime(2023, 2, 4),
            ),
        )
        ctx = self.client.get(self.url).context_data
        transfer = ctx["slices"][0]
        self.assertEqual(
            len(transfer.contact_transfers), 0
        )

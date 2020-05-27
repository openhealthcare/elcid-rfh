from unittest import mock
from django.test import override_settings
from opal.core.test import OpalTestCase
from elcid.management.commands import check_disk_space

@mock.patch("elcid.management.commands.check_disk_space.send_mail")
@override_settings(OPAL_BRAND_NAME="RFH")
class CheckDiskSpaceTestCase(OpalTestCase):
    def test_raise_the_alarm(self, send_mail):
        check_disk_space.raise_the_alarm()
        self.assertEqual(
            send_mail.call_args[0][0],
            "RFH Disk Space Alert: Action Required"
        )
        expected = "Routine system check on RFH has detected a volume with > 90% disk usage. Please log in and investigate."
        self.assertEqual(
            send_mail.call_args[0][1],
            expected
        )



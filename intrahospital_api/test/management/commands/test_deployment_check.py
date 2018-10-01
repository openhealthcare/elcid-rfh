import mock
import datetime
from django.utils import timezone as tz
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import deployment_check
from intrahospital_api.deployment_check import RollBackError


@mock.patch(
    "intrahospital_api.management.commands.deployment_check.deployment_check.check_since"
)
@mock.patch(
    "intrahospital_api.management.commands.deployment_check.six"
)
@mock.patch(
    "intrahospital_api.management.commands.deployment_check.timezone"
)
class DeploymentCheckTestCase(OpalTestCase):
    def test_prints_result(self, timezone, six, check_since):
        def dep_check_side_effect(x, result):
            result["current"] = 1
            raise RollBackError("roll back")

        timezone.now.return_value = tz.make_aware(
            datetime.datetime(2017, 1, 1, 5)
        )

        # by default this should be four hours before tz.now
        expected_dt = tz.make_aware(datetime.datetime(2017, 1, 1, 1))

        cmd = deployment_check.Command()
        check_since.side_effect = dep_check_side_effect
        cmd.handle(hours=4)
        six._print.assert_called_once_with({"current": 1})
        # interestingly mock stores a reference so its
        # passed in an empty dictionary but because its a reference
        # this, to mock, looks like the result of the dict
        check_since.assert_called_once_with(
            expected_dt, {"current": 1}
        )

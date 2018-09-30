import mock
from opal.core.test import OpalTestCase
from intrahospital_api.management.commands import deployment_check
from intrahospital_api.deployment_check import RollBackError


@mock.patch(
    "intrahospital_api.management.commands.deployment_check.deployment_check.check_since"
)
@mock.patch(
    "intrahospital_api.management.commands.deployment_check.six"
)
class DeploymentCheckTestCase(OpalTestCase):
    def test_prints_result(self, six, check_since):
        def dep_check_side_effect(x, result):
            result["current"] = 1
            raise RollBackError("roll back")

        cmd = deployment_check.Command()
        check_since.side_effect = dep_check_side_effect
        cmd.handle()
        six._print.assert_called_once_with({"current": 1})

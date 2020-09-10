from unittest import mock
from opal.core.test import OpalTestCase
from elcid.patient_lists import Bacteraemia
from plugins.labtests.management.commands import check_lab_test_counts

path = "plugins.labtests.management.commands.check_lab_test_counts"
email_title = "elCID Royal Free Hospital ICU & Bacteraemia lab test counts"
email_title_warning = (
    "elCID Royal Free Hospital ICU & Bacteraemia lab test counts WARNING"
)

@mock.patch("{}.logger".format(path))
class CheckLabTestsTestCase(OpalTestCase):
    @mock.patch("{}.send_email".format(path))
    @mock.patch("{}.loader.sync_patient".format(path))
    def test_handle_none(self, sync_patient, send_email, logger):
        cmd = check_lab_test_counts.Command()
        cmd.handle()
        ctx = {
            "table_context": {
                "Patient count": 0,
                "Before patient sync count": 0,
                "After patient sync count": 0,
            },
            "title": email_title,
        }
        send_email.assert_called_once_with(
            email_title,
            "email/table_email.html",
            ctx,
        )

    @mock.patch("{}.send_email".format(path))
    @mock.patch("{}.loader.sync_patient".format(path))
    def test_handle_changed(self, sync_patient, send_email, logger):
        patient, episode = self.new_patient_and_episode_please()
        episode.set_tag_names([Bacteraemia.tag], None)
        lt = patient.lab_tests.create()
        lt.observation_set.create()

        def create_obs(x):
            lt.observation_set.create()

        sync_patient.side_effect = create_obs
        cmd = check_lab_test_counts.Command()
        cmd.handle()
        ctx = {
            "table_context": {
                "Patient count": 1,
                "Before patient sync count": 1,
                "After patient sync count": 2,
            },
            "title": "elCID Royal Free Hospital ICU & Bacteraemia lab test counts WARNING",
            "title": email_title_warning,
        }
        send_email.assert_called_once_with(
            email_title_warning,
            "email/table_email.html",
            ctx,
        )

    @mock.patch("{}.send_mail".format(path))
    @mock.patch("{}.loader.sync_patient".format(path))
    def test_template_compile(self, sync_patient, send_mail, logger):
        cmd = check_lab_test_counts.Command()
        cmd.handle()
        html_message = send_mail.call_args[1]["html_message"]
        expected = """
<html>
<body>
  <h1>elCID Royal Free Hospital ICU &amp; Bacteraemia lab test counts</h1>
  <table width="600" cellpadding="0" cellspacing="0" border="0">

    <tr>
      <td style="text-align: center;">Patient count</td>
      <td style="text-align: center;">0</td>
    </tr>

    <tr>
      <td style="text-align: center;">Before patient sync count</td>
      <td style="text-align: center;">0</td>
    </tr>

    <tr>
      <td style="text-align: center;">After patient sync count</td>
      <td style="text-align: center;">0</td>
    </tr>

  </table>
</body>
</html>"""
        # lets ignore white space
        clean_expected = "".join([i.strip() for i in expected.split("\n")])
        clean_html_message = "".join([i.strip() for i in html_message.split("\n")])
        self.assertEqual(clean_expected, clean_html_message)
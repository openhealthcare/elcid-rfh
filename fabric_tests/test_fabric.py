""" A wise man once said, is there any point in testing
    files where you're just calling system calls and everything is mocked.

    And he was wise.

    We think there probably is, just to reassure one of their pythonic
    assumptions.

    Obviously its not as good as running it for realsies
"""

import tempfile
import os
import sys
import mock
import datetime
from opal.core.test import OpalTestCase

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fabfile


@mock.patch("fabfile.local")
class CloneBranchTestCase(OpalTestCase):
    def test_clone_branch(self, local):
        branch_name = "some-branch"
        expected = "git clone -b some-branch \
https://github.com/openhealthcare/elcid-rfh \
/usr/local/ohc/elcidrfh-some-branch"
        fabfile.clone_branch(branch_name)
        local.assert_called_once_with(expected)


@mock.patch("fabfile.json")
class CreatePrivateSettingsTestCase(OpalTestCase):
    def test_create_private_settings(self, json):
        m = mock.mock_open()
        fab_open = "fabfile.open"
        with mock.patch(fab_open, m, create=True):
            fabfile.create_private_settings()
        called = json.dump.call_args[0][0]
        self.assertEqual(
            called,
            dict(
                proxy="",
                db_password="",
                host_string="",
                additional_settings={}
            )
        )
        m.assert_called_once_with('/usr/local/ohc/private_settings.json', 'w')


class FabfileTestCase(OpalTestCase):
    def setUp(self):
        self.env = fabfile.Env("some_branch")


class EnvTestCase(FabfileTestCase):
    def test_project_directory(self):
        self.assertEqual(
            self.env.project_directory,
            "/usr/local/ohc/elcidrfh-some_branch"
        )

    def test_release_name(self):
        self.assertEqual(
            self.env.release_name,
            "elcidrfh-some_branch"
        )

    def test_virtual_env_path(self):
        self.assertEqual(
            self.env.virtual_env_path,
            "/home/ohc/.virtualenvs/elcidrfh-some_branch"
        )

    def test_database_name(self):
        self.assertEqual(
            self.env.database_name,
            "elcidrfh_some_branch"
        )

    @mock.patch("fabfile.datetime")
    def test_backup_name(self, dt):
        dt.datetime.now.return_value = datetime.datetime(
            2017, 9, 7, 11, 12
        )
        self.assertEqual(
            self.env.backup_name,
            "/usr/local/ohc/var/back.07.09.2017.elcidrfh_some_branch.sql"
        )
        self.assertTrue(dt.datetime.now.called)

    @mock.patch("fabfile.datetime")
    def test_release_backup_name(self, dt):
        dt.datetime.now.return_value = datetime.datetime(
            2017, 9, 7, 11, 12
        )
        self.assertEqual(
            self.env.release_backup_name,
            "/usr/local/ohc/var/release.07.09.2017.11.\
12.elcidrfh_some_branch.sql"
        )
        self.assertTrue(dt.datetime.now.called)


@mock.patch("fabfile.local")
@mock.patch("fabfile.lcd")
class RunManagementCommandTestCase(FabfileTestCase):
    def test_run_management_command(self, lcd, local):
        local.return_value = "something"
        result = fabfile.run_management_command("some_command", self.env)
        local.called_once_with("as")
        self.assertEqual(result, "something")
        lcd.assert_called_once_with("/usr/local/ohc/elcidrfh-some_branch")


@mock.patch("fabfile.local")
class PipTestCase(FabfileTestCase):
    def test_pip_create_virtual_env(self, local):
        fabfile.pip_create_virtual_env(self.env)
        first_call = local.call_args_list[0][0][0]
        self.assertEqual(
            first_call,
            "rm -rf /home/ohc/.virtualenvs/elcidrfh-some_branch"
        )
        second_call = local.call_args_list[1][0][0]
        self.assertEqual(
            second_call,
            "/usr/bin/virtualenv /home/ohc/.virtualenvs/elcidrfh-some_branch"
        )

    def test_pip_install_requirements(self, local):
        fabfile.pip_install_requirements(self.env, "some_proxy")
        first_call = local.call_args_list[0][0][0]
        self.assertEqual(
            first_call,
            "/home/ohc/.virtualenvs/elcidrfh-some_branch/bin/pip install \
--upgrade pip"
        )
        second_call = local.call_args_list[1][0][0]
        self.assertEqual(
            second_call,
            "/home/ohc/.virtualenvs/elcidrfh-some_branch/bin/pip install -r \
requirements.txt"
        )

    def test_set_project_directory(self, local):
        fabfile.pip_set_project_directory(self.env)
        local.assert_called_once_with(
            "echo '/usr/local/ohc/elcidrfh-some_branch' > \
/home/ohc/.virtualenvs/elcidrfh-some_branch/.project"
        )


@mock.patch("fabfile.local")
class PostgresTestCase(FabfileTestCase):
    def test_postgres_command(self, local):
        local.return_value = "something"
        result = fabfile.postgres_command("some_command", capture=True)
        self.assertEqual(result, "something")
        local.assert_called_once_with(
            'sudo -u postgres psql --command "some_command"',
            capture=True
        )

    def test_progres_create_database_with_drop(self, local):
        local.return_value = "1"
        fabfile.postgres_create_database(self.env)
        call_args = local.call_args_list
        self.assertEqual(len(call_args), 4)
        self.assertEqual(
            call_args[0][0][0],
            "sudo -u postgres psql -lqt | cut -d \| -f 1 | \
grep -w elcidrfh_some_branch | wc -l"
        )

        self.assertEqual(
            call_args[1][0][0],
            'sudo -u postgres psql --command "DROP DATABASE \
elcidrfh_some_branch"'
        )

        self.assertEqual(
            call_args[2][0][0],
            'sudo -u postgres psql --command "CREATE DATABASE \
elcidrfh_some_branch"'
        )

        self.assertEqual(
            call_args[3][0][0],
            'sudo -u postgres psql --command "GRANT ALL PRIVILEGES ON \
DATABASE elcidrfh_some_branch TO ohc"'
        )

    def test_progres_create_database_without_drop(self, local):
        local.return_value = "0"
        fabfile.postgres_create_database(self.env)
        call_args = local.call_args_list

        self.assertEqual(len(call_args), 3)
        self.assertEqual(
            call_args[0][0][0],
            "sudo -u postgres psql -lqt | cut -d \| -f 1 | \
grep -w elcidrfh_some_branch | wc -l"
        )

        self.assertEqual(
            call_args[1][0][0],
            'sudo -u postgres psql --command "CREATE DATABASE \
elcidrfh_some_branch"'
        )

        self.assertEqual(
            call_args[2][0][0],
            'sudo -u postgres psql --command "GRANT ALL PRIVILEGES ON \
DATABASE elcidrfh_some_branch TO ohc"'
        )

    @mock.patch('fabfile.os')
    def test_postgres_load_database_if_it_doesnt_exists(self, os, local):
        os.path.isfile.return_value = False
        with self.assertRaises(ValueError) as er:
            fabfile.postgres_load_database("some_backup_full_path", self.env)

        self.assertEqual(
            str(er.exception),
            "unable to find a backup at some_backup_full_path"
        )
        os.path.isfile.assert_called_once_with("some_backup_full_path")

    @mock.patch('fabfile.os')
    def test_postgres_load_database_if_exists(self, os, local):
        os.path.isfile.return_value = True
        fabfile.postgres_load_database("some_backup_full_path", self.env)
        local.assert_called_once_with(
            "sudo -u postgres psql -d elcidrfh_some_branch -f \
some_backup_full_path"
        )


class ServicesTestCase(FabfileTestCase):
    @mock.patch('fabfile.os')
    def test_services_symlink_nginx_if_it_doesnt_exists(self, os):
        os.path.isfile.return_value = False
        with self.assertRaises(ValueError) as er:
            fabfile.services_symlink_nginx(self.env)

        self.assertEqual(
            str(er.exception),
            "we expect an nginx conf to exist at \
/usr/local/ohc/elcidrfh-some_branch/etc/nginx.conf"
        )

        os.path.isfile.assert_called_once_with(
            "/usr/local/ohc/elcidrfh-some_branch/etc/nginx.conf"
        )

    @mock.patch('fabfile.local')
    @mock.patch('fabfile.os')
    def test_services_symlink_nginx_if_exists(self, os, local):
        os.path.isfile.return_value = True
        fabfile.services_symlink_nginx(self.env)

        os.path.isfile.assert_called_once_with(
            "/usr/local/ohc/elcidrfh-some_branch/etc/nginx.conf"
        )
        first_call = local.call_args_list[0][0][0]
        self.assertEqual(
            first_call,
            "sudo rm /etc/nginx/sites-enabled/elcidrfh-some_branch"
        )

        second = local.call_args_list[1][0][0]
        self.assertEqual(
            second,
            "sudo ln -s /usr/local/ohc/elcidrfh-some_branch/etc/nginx.conf \
/etc/nginx/sites-enabled/elcidrfh-some_branch"
        )

    @mock.patch('fabfile.os')
    def test_services_symlink_upstart_if_it_doesnt_exists(self, os):
        os.path.isfile.return_value = False
        with self.assertRaises(ValueError) as er:
            fabfile.services_symlink_upstart(self.env)

        self.assertEqual(
            str(er.exception),
            "we expect an upstart conf to exist \
/usr/local/ohc/elcidrfh-some_branch/etc/upstart.conf"
        )

        os.path.isfile.assert_called_once_with(
            "/usr/local/ohc/elcidrfh-some_branch/etc/upstart.conf"
        )

    @mock.patch('fabfile.local')
    @mock.patch('fabfile.os')
    def test_services_symlink_upstart_if_exists(self, os, local):
        os.path.isfile.return_value = True
        fabfile.services_symlink_upstart(self.env)

        os.path.isfile.assert_called_once_with(
            "/usr/local/ohc/elcidrfh-some_branch/etc/upstart.conf"
        )
        first_call = local.call_args_list[0][0][0]
        self.assertEqual(
            first_call,
            "sudo rm -f /etc/init/elcid.conf"
        )

        second = local.call_args_list[1][0][0]
        self.assertEqual(
            second,
            "sudo ln -s /usr/local/ohc/elcidrfh-some_branch/etc/upstart.conf \
/etc/init/elcid.conf"
        )

    @mock.patch('fabfile.local')
    def test_sevices_create_local_settings(self, local):
        some_dir = tempfile.mkdtemp()
        project_dir = "{}/elcid".format(some_dir)
        os.mkdir(project_dir)
        with mock.patch(
            "fabfile.Env.project_directory", new_callable=mock.PropertyMock
        ) as prop:
            prop.return_value = some_dir
            private_settings = dict(
                additional_settings={"Some": "'settings'"}
            )
            fabfile.services_create_local_settings(
                self.env, private_settings
            )

        local_settings_file = "{}/local_settings.py".format(project_dir)
        with open(local_settings_file) as l:
            output_file = l.read()

        self.assertIn("Some = 'settings'", output_file)
        self.assertIn("'NAME': 'elcidrfh_some_branch'", output_file)

        local.assert_called_once_with(
            "rm -f {}".format(local_settings_file)
        )

    @mock.patch('fabfile.local')
    def test_services_create_gunicorn_settings(self, local):
        some_dir = tempfile.mkdtemp()
        project_dir = "{}/etc".format(some_dir)
        os.mkdir(project_dir)
        with mock.patch(
            "fabfile.Env.project_directory", new_callable=mock.PropertyMock
        ) as prop:
            prop.return_value = some_dir
            fabfile.services_create_gunicorn_settings(
                self.env
            )

        gunicorn_conf_file = "{}/gunicorn.conf".format(project_dir)
        with open(gunicorn_conf_file) as l:
            output_file = l.read()

        # make sure we're executing gunicorn with our project directory
        self.assertIn("elcidrfh-some_branch/bin/gunicorn", output_file)
        local.assert_called_once_with(
            "rm -f {}".format(gunicorn_conf_file)
        )


@mock.patch('fabfile.local')
class RestartTestCase(FabfileTestCase):
    def test_restart_supervisord(self, local):
        fabfile.restart_supervisord(self.env)
        local.assert_called_once_with(
            "/home/ohc/.virtualenvs/elcidrfh-some_branch/bin/supervisorctl \
-c etc/supervisord.conf restart all")

    def test_restart_nginx(self, local):
        fabfile.restart_nginx()
        local.assert_called_once_with("sudo /etc/init.d/nginx restart")


@mock.patch('fabfile.local')
class CronTestCase(FabfileTestCase):
    def test_cron_write_backup(self, local):
        fabfile.cron_write_backup(self.env)
        local.assert_called_once_with('echo \'0 2 * * * postgres pg_dump elcidrfh_some_branch \
> /usr/local/ohc/var/back.$(date +"%d.%m.%Y").elcidrfh_some_branch.sql\' | \
sudo tee /etc/cron.d/elcid_backup')

    def test_cron_copy_backup(self, local):
        fabfile.cron_copy_backup(self.env)
        local.assert_called_once_with("echo '0 2 * * * ohc \
/home/ohc/.virtualenvs/elcidrfh-some_branch/bin/fab -f \
/Users/fredkingham/Scripts/ohcdev/src/elcid-rfh/fabfile.py \
copy_backup:elcidrfh_some_branch' | sudo tee /etc/cron.d/elcid_copy")


@mock.patch("fabfile.get_private_settings")
@mock.patch("fabfile.run_management_command")
@mock.patch("fabfile.put")
@mock.patch("fabfile.env")
@mock.patch("fabfile.os")
class CopyBackupTestCase(FabfileTestCase):
    def test_copy_backup(
        self, os, env, put, run_management_command, get_private_settings
    ):
        get_private_settings.return_value(dict(
            host_string="121.1.1.1",
            password="some_password"
        ))
        os.path.isfile.return_value = True
        fabfile.copy_backup(self.env.branch)
        p = "/usr/local/ohc/var/back.07.09.2017.elcidrfh_some_branch.sql"
        put.assert_called_once_with(
            local_path=p,
            remote_path=p
        )

    def test_copy_backup_no_backup(
        self, os, env, put, run_management_command, get_private_settings
    ):
        get_private_settings.return_value(dict(
            host_string="121.1.1.1",
            password="some_password"
        ))
        os.path.isfile.return_value = False

        with mock.patch(
            "fabfile.Env.backup_name", new_callable=mock.PropertyMock
        ) as prop:
            prop.return_value = "some_backup"
            fabfile.copy_backup(self.env.branch)

        self.assertEqual(
            run_management_command.call_args[0][0],
            "send error 'unable to find backup some_backup'"
        )

    def test_put_raises_exception(
        self, os, env, put, run_management_command, get_private_settings
    ):
        get_private_settings.return_value(dict(
            host_string="121.1.1.1",
            password="some_password"
        ))
        put.side_effect = ValueError("failed")
        with mock.patch(
            "fabfile.Env.backup_name", new_callable=mock.PropertyMock
        ) as prop:
            prop.return_value = "some_backup"
            fabfile.copy_backup(self.env.branch)

        self.assertEqual(
            run_management_command.call_args[0][0],
            "send error 'unable to copy backup some_backup' with 'failed'"
        )


@mock.patch("fabfile.json")
@mock.patch("fabfile.os")
class GetPrivateSettingsTestCase(OpalTestCase):
    def test_unable_to_find_file(self, os, json):
        os.path.isfile.return_value = False

        with self.assertRaises(ValueError) as e:
            fabfile.get_private_settings()

        self.assertEqual(
            str(e.exception),
            "unable to find additional settings at \
/usr/local/ohc/private_settings.json"
        )

    def test_db_password_not_present(self, os, json):
        m = mock.mock_open()
        fab_open = "fabfile.open"
        json.load.return_value = {}
        with mock.patch(fab_open, m, create=True):
            with self.assertRaises(ValueError) as e:
                fabfile.get_private_settings()

        self.assertEqual(
            str(e.exception),
            "we require a db password in your private settings"
        )

    def test_additional_settings_present(self, os, json):
        m = mock.mock_open()
        fab_open = "fabfile.open"
        json.load.return_value = dict(
            db_password="something"
        )
        with mock.patch(fab_open, m, create=True):
            with self.assertRaises(ValueError) as e:
                fabfile.get_private_settings()

        self.assertEqual(
            str(e.exception),
            "we require an additional_settings dict (even if its empty) in \
your private settings"
        )

    def test_proxy_present(self, os, json):
        m = mock.mock_open()
        fab_open = "fabfile.open"
        json.load.return_value = dict(
            db_password="something",
            additional_settings={}
        )
        with mock.patch(fab_open, m, create=True):
            with self.assertRaises(ValueError) as e:
                fabfile.get_private_settings()

        self.assertEqual(
            str(e.exception),
            "we require proxy variable in your private settings"
        )

    def test_host_string(self, os, json):
        m = mock.mock_open()
        fab_open = "fabfile.open"
        json.load.return_value = dict(
            db_password="something",
            additional_settings={},
            proxy="127.0.0.1"
        )
        with mock.patch(fab_open, m, create=True):
            with self.assertRaises(ValueError) as e:
                fabfile.get_private_settings()

        self.assertEqual(
            str(e.exception),
            "we host string to be set, this should be 127.0.0.1 on test, or \
the address you want to sync to on prod in your private settings"
        )

    def test_get_private_settings(self, os, json):
        m = mock.mock_open()
        fab_open = "fabfile.open"
        expected = dict(
            db_password="something",
            additional_settings={},
            proxy="127.0.0.1",
            host_string="some_str"
        )
        json.load.return_value = expected
        with mock.patch(fab_open, m, create=True):
            result = fabfile.get_private_settings()

        self.assertEqual(result, expected)

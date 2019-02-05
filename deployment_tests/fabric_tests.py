""" A wise man once said, is there any point in testing
    files where you're just calling system calls and everything is mocked.

    And he was wise.

    We think there probably is, just to reassure one of their pythonic
    assumptions.

    Obviously its not as good as running it for realsies
"""
import json
import tempfile
import os
import sys
import mock
import datetime
import unittest

import fabfile
from fabfile import Env


class FakeFabricCapture(object):
    def __init__(self, some_str, stdout=None, stderr=None, failed=None):
        self.some_str = some_str
        self.stdout = stdout or some_str
        self.stderr = stderr
        self.failed = failed

    def __str__(self):
        return self.some_str


@mock.patch("fabfile.local")
@mock.patch("fabfile.os")
@mock.patch("fabfile.print", create=True)
class CloneBranchTestCase(unittest.TestCase):
    def test_clone_branch(self, print_statement, os, local):
        os.path.isdir.return_value = False
        branch_name = "some-branch"
        expected = "git clone -b some-branch \
https://github.com/openhealthcare/elcid-rfh \
/usr/lib/ohc/elcidrfh-some-branch"
        fabfile.clone_branch(branch_name)
        print_statement.assert_called_once_with(
            'Cloning into /usr/lib/ohc/elcidrfh-some-branch'
        )
        local.assert_called_once_with(expected)

    def test_clone_branch_raises(self, print_statement, os, local):
        os.path.isdir.return_value = True
        branch_name = "some-branch"
        with self.assertRaises(ValueError) as err:
            fabfile.clone_branch(branch_name)
        self.assertEqual(
            str(err.exception),
            "/usr/lib/ohc/elcidrfh-some-branch already exists"
        )


@mock.patch("fabfile.json")
@mock.patch("fabfile.os")
class CreatePrivateSettingsTestCase(unittest.TestCase):
    def test_create_private_settings(self, os, json):
        m = mock.mock_open()
        os.path.isfile.return_value = False
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
                additional_settings={},
                remote_password=""
            )
        )
        m.assert_called_once_with('/usr/lib/ohc/private_settings.json', 'w')

    def test_private_settings_already_exist(self, os, json):
        # mock open just in case, we don't want to
        # accidentally write anything
        os.path.isfile.return_value = True
        er = "private settings already exist at \
/usr/lib/ohc/private_settings.json"
        with self.assertRaises(ValueError) as err:
            fabfile.create_private_settings()
        self.assertEqual(
            str(err.exception), er
        )


class FabfileTestCase(unittest.TestCase):
    def setUp(self):
        self.env = fabfile.Env("some_branch")
        # test env deletes the existing environment
        self.test_env = fabfile.Env("some_branch")


@mock.patch("fabfile.local")
@mock.patch("fabfile.pip_create_virtual_env")
@mock.patch("fabfile.get_private_settings")
class TestCreateDeploymentEnv(unittest.TestCase):
    def test_pip_create_deployment_env(
        self, get_private_settings, pip_create_virtual_env, local
    ):
        env = fabfile.Env("some_branch")
        get_private_settings.return_value = dict(proxy="blah")
        fabfile.pip_create_deployment_env("some_branch")
        pip_create_virtual_env.assert_called_once_with(
            env.deployment_env_path, remove_existing=True
        )
        call_args_list = local.call_args_list
        self.assertEqual(
            call_args_list[0][0][0],
            "{}/bin/pip install pip==9.0.1 --proxy blah".format(
                env.deployment_env_path
            )
        )
        self.assertEqual(
            call_args_list[1][0][0],
            "{}/bin/pip install -r requirements-deployment.txt --proxy blah".format(
                env.deployment_env_path
            )
        )


class EnvTestCase(FabfileTestCase):
    def test_project_directory(self):
        self.assertEqual(
            self.env.project_directory,
            "/usr/lib/ohc/elcidrfh-some_branch"
        )

    @mock.patch("fabfile.datetime")
    def test_remote_backup_name(self, dt):
        dt.datetime.now.return_value = datetime.datetime(2017, 9, 21)
        prod_env = fabfile.Env("some_branch")
        self.assertEqual(
            prod_env.remote_backup_name,
            "/usr/lib/ohc/var/live/back.21.09.2017.elcidrfh_some_branch.sql"
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
        prod_env = fabfile.Env("some_branch")
        self.assertEqual(
            prod_env.backup_name,
            "/usr/lib/ohc/var/back.07.09.2017.elcidrfh_some_branch.sql"
        )
        self.assertTrue(dt.datetime.now.called)

    @mock.patch("fabfile.datetime")
    def test_release_backup_name(self, dt):
        dt.datetime.now.return_value = datetime.datetime(
            2017, 9, 7, 11, 12
        )
        prod_env = fabfile.Env("some_branch")
        self.assertEqual(
            prod_env.release_backup_name,
            "/usr/lib/ohc/var/release.07.09.2017.11.\
12.elcidrfh_some_branch.sql"
        )
        self.assertTrue(dt.datetime.now.called)


@mock.patch('fabfile.os')
class InferCurrentBranchTestCase(FabfileTestCase):
    def test_infer_current_branch_success(self, os):
        os.path.abspath.return_value = "/usr/lib/ohc/elcidrfh-something"
        self.assertEqual(
            fabfile.infer_current_branch(),
            "something"
        )

    def test_infer_current_branch_error(self, os):
        os.path.abspath.return_value = "/usr/lib/ohc/blah"
        with self.assertRaises(ValueError) as er:
            fabfile.infer_current_branch(),

        expected = "we are in /usr/lib/ohc/blah but expect to be in a \
directory beginning with /usr/lib/ohc/elcidrfh-"
        self.assertEqual(str(er.exception), expected)


@mock.patch("fabfile.local")
@mock.patch("fabfile.lcd")
@mock.patch("fabfile.print", create=True)
class RunManagementCommandTestCase(FabfileTestCase):
    def test_run_management_command(self, print_statement, lcd, local):
        local.return_value = FakeFabricCapture("something")
        result = fabfile.run_management_command("some_command", self.env)
        local.called_once_with("as")
        self.assertEqual(result, local.return_value)
        lcd.assert_called_once_with("/usr/lib/ohc/elcidrfh-some_branch")


@mock.patch("fabfile.print", create=True)
@mock.patch("fabfile.local")
class PipTestCase(FabfileTestCase):

    @mock.patch("fabfile.os")
    def test_pip_prod_create_virtual_env(self, os, local, print_statment):
        os.path.isdir.return_value = True
        with self.assertRaises(ValueError) as er:
            fabfile.pip_create_virtual_env(self.env.virtual_env_path, False)

        os.path.isdir.assert_called_once_with(
            "/home/ohc/.virtualenvs/elcidrfh-some_branch"
        )
        self.assertEqual(
            str(er.exception),
            "Directory /home/ohc/.virtualenvs/elcidrfh-some_branch already \
exists"
        )

    def test_pip_test_create_virtual_env_with_remove(
        self, local, print_statement
    ):
        fabfile.pip_create_virtual_env(self.test_env.virtual_env_path, True)
        print_statement.assert_called_once_with("Creating new environment")
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

    def test_pip_test_create_virtual_env_without_remove(
        self, local, print_statement
    ):
        fabfile.pip_create_virtual_env(self.env.virtual_env_path, False)
        local.assert_called_once_with(
            "/usr/bin/virtualenv /home/ohc/.virtualenvs/elcidrfh-some_branch"
        )

    def test_pip_install_requirements(self, local, print_statement):
        fabfile.pip_install_requirements(
            self.env, "some_proxy"
        )
        first_call = local.call_args_list[0][0][0]
        self.assertEqual(
            first_call,
            "/home/ohc/.virtualenvs/elcidrfh-some_branch/bin/pip install \
pip==18.0 --proxy some_proxy"
        )
        second_call = local.call_args_list[1][0][0]
        self.assertEqual(
            second_call,
            '/home/ohc/.virtualenvs/elcidrfh-some_branch/bin/pip install \
requests==2.20.1 --proxy some_proxy'
        )


        third_call = local.call_args_list[2][0][0]
        self.assertEqual(
            third_call,
            "/home/ohc/.virtualenvs/elcidrfh-some_branch/bin/pip install -r \
requirements.txt --proxy some_proxy"
        )

    def test_set_project_directory(self, local, print_statement):
        fabfile.pip_set_project_directory(self.env)
        local.assert_called_once_with(
            "echo '/usr/lib/ohc/elcidrfh-some_branch' > \
/home/ohc/.virtualenvs/elcidrfh-some_branch/.project"
        )


@mock.patch("fabfile.print", create=True)
@mock.patch("fabfile.local")
class PostgresTestCase(FabfileTestCase):
    def test_postgres_on_prod_raises(self, local, print_function):
        local.return_value = FakeFabricCapture(
            "1", stdout="1", stderr="no problem"
        )
        with self.assertRaises(ValueError) as err:
            fabfile.postgres_create_database(self.env, False)
        first_call = print_function.call_args_list[0][0][0]
        self.assertEqual(
            first_call,
            "Creating the database"
        )

        second_call = print_function.call_args_list[1][0][0]
        self.assertEqual(
            second_call,
            "no problem"
        )

        third_call = print_function.call_args_list[2][0][0]
        self.assertEqual(
            third_call,
            "1"
        )
        self.assertEqual(
            str(err.exception),
            "database elcidrfh_some_branch already exists"
        )

    def test_progres_create_database_with_test_database_found(
        self, local, print_function
    ):
        local.return_value = FakeFabricCapture("1")
        fabfile.postgres_create_database(self.test_env, True)
        call_args = local.call_args_list
        self.assertEqual(len(call_args), 4)
        self.assertEqual(
            call_args[0][0][0],
            'sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE \
datname=\'elcidrfh_some_branch\'"'
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

    def test_progres_create_database_without_drop(
        self, local, print_function
    ):
        local.return_value = FakeFabricCapture("0")
        fabfile.postgres_create_database(self.env, True)
        call_args = local.call_args_list

        self.assertEqual(len(call_args), 3)
        self.assertEqual(
            call_args[0][0][0],
            'sudo -u postgres psql -tAc "SELECT 1 FROM pg_database \
WHERE datname=\'elcidrfh_some_branch\'"'
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
    def test_postgres_load_database_if_exists(
        self, os, local, print_function
    ):
        os.path.isfile.return_value = True
        fabfile.postgres_load_database("some_backup_full_path", self.env)
        local.assert_called_once_with(
            "sudo -u postgres psql -d elcidrfh_some_branch -f \
some_backup_full_path"
        )
        print_function.assert_called_once_with(
            "Loading the database elcidrfh_some_branch"
        )


@mock.patch("fabfile.print", create=True)
class ServicesTestCase(FabfileTestCase):
    @mock.patch('fabfile.os')
    def test_services_symlink_nginx_if_it_doesnt_exists(
        self, os, print_function
    ):
        os.path.isfile.return_value = False
        with self.assertRaises(ValueError) as er:
            fabfile.services_symlink_nginx(self.env)

        print_function.assert_called_once_with(
            "Symlinking nginx"
        )

        self.assertEqual(
            str(er.exception),
            "we expect an nginx conf to exist at \
/usr/lib/ohc/elcidrfh-some_branch/etc/nginx.conf"
        )

        os.path.isfile.assert_called_once_with(
            "/usr/lib/ohc/elcidrfh-some_branch/etc/nginx.conf"
        )

    @mock.patch('fabfile.local')
    @mock.patch('fabfile.os')
    def test_services_symlink_nginx_if_exists(
        self, os, local, print_function
    ):
        os.path.isfile.return_value = True
        fabfile.services_symlink_nginx(self.env)

        os.path.isfile.assert_called_once_with(
            "/usr/lib/ohc/elcidrfh-some_branch/etc/nginx.conf"
        )
        first_call = local.call_args_list[0][0][0]
        self.assertEqual(
            first_call,
            "sudo rm /etc/nginx/sites-enabled/elcid"
        )

        second = local.call_args_list[1][0][0]

        self.assertEqual(
            second,
            "sudo rm /etc/nginx/sites-enabled/elcid-rfh"
        )

        third = local.call_args_list[2][0][0]
        self.assertEqual(
            third,
            "sudo ln -s /usr/lib/ohc/elcidrfh-some_branch/etc/nginx.conf \
/etc/nginx/sites-enabled/elcid"
        )

    @mock.patch('fabfile.os')
    def test_services_symlink_upstart_if_it_doesnt_exists(
        self, os, print_function
    ):
        os.path.isfile.return_value = False
        with self.assertRaises(ValueError) as er:
            fabfile.services_symlink_upstart(self.env)

        print_function.assert_called_once_with("Symlinking upstart")
        self.assertEqual(
            str(er.exception),
            "we expect an upstart conf to exist \
/usr/lib/ohc/elcidrfh-some_branch/etc/upstart.conf"
        )

        os.path.isfile.assert_called_once_with(
            "/usr/lib/ohc/elcidrfh-some_branch/etc/upstart.conf"
        )

    @mock.patch('fabfile.local')
    @mock.patch('fabfile.os')
    def test_services_symlink_upstart_if_exists(
        self, os, local, print_function
    ):
        os.path.isfile.return_value = True
        fabfile.services_symlink_upstart(self.env)

        os.path.isfile.assert_called_once_with(
            "/usr/lib/ohc/elcidrfh-some_branch/etc/upstart.conf"
        )
        first_call = local.call_args_list[0][0][0]
        self.assertEqual(
            first_call,
            "sudo rm -f /etc/init/elcid.conf"
        )

        second = local.call_args_list[1][0][0]
        self.assertEqual(
            second,
            "sudo ln -s /usr/lib/ohc/elcidrfh-some_branch/etc/upstart.conf \
/etc/init/elcid.conf"
        )

    @mock.patch('fabfile.local')
    def test_sevices_create_local_settings(
        self, local, print_function
    ):
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
    def test_services_create_gunicorn_conf(
        self, local, print_function
    ):
        some_dir = tempfile.mkdtemp()
        project_dir = "{}/etc".format(some_dir)
        os.mkdir(project_dir)
        with mock.patch(
            "fabfile.Env.project_directory", new_callable=mock.PropertyMock
        ) as prop:
            prop.return_value = some_dir
            fabfile.services_create_gunicorn_conf(
                self.env
            )
        print_function.assert_called_once_with('Creating gunicorn conf')
        gunicorn_conf_file = "{}/gunicorn.conf".format(project_dir)
        with open(gunicorn_conf_file) as l:
            output_file = l.read()

        # make sure we're executing gunicorn with our project directory
        self.assertIn("elcidrfh-some_branch/bin/gunicorn", output_file)
        local.assert_called_once_with(
            "rm -f {}".format(gunicorn_conf_file)
        )

    @mock.patch('fabfile.local')
    def test_services_create_upstart_conf(self, local, print_function):
        some_dir = tempfile.mkdtemp()
        project_dir = "{}/etc".format(some_dir)
        os.mkdir(project_dir)
        with mock.patch(
            "fabfile.Env.project_directory", new_callable=mock.PropertyMock
        ) as prop:
            prop.return_value = some_dir
            fabfile.services_create_upstart_conf(
                self.env
            )

        upstart_conf_file = "{}/upstart.conf".format(project_dir)
        with open(upstart_conf_file) as l:
            output_file = l.read()
        print_function.assert_called_once_with('Creating upstart conf')
        # make sure we're executing gunicorn with our project directory
        self.assertIn("elcidrfh-some_branch-deployment/bin/activate;", output_file)
        local.assert_called_once_with(
            "rm -f {}".format(upstart_conf_file)
        )


@mock.patch('fabfile.print', create=True)
@mock.patch('fabfile.local')
class RestartTestCase(FabfileTestCase):
    def test_restart_supervisord(
        self, local, print_function
    ):
        fabfile.restart_supervisord(self.env)
        print_function.assert_called_once_with("Restarting supervisord")
        first_call = local.call_args_list[0][0][0]
        expected_first_call = "/home/ohc/.virtualenvs/elcidrfh-some_branch-deployment/bin\
/supervisord -c /usr/lib/ohc/elcidrfh-some_branch/etc/production.conf"
        self.assertEqual(first_call, expected_first_call)

    def test_restart_nginx(self, local, print_function):
        fabfile.restart_nginx()
        print_function.assert_called_once_with('Restarting nginx')
        local.assert_called_once_with("sudo service nginx restart")


@mock.patch('fabfile.local')
@mock.patch('fabfile.print', create=True)
class CronTestCase(FabfileTestCase):
    def test_write_cron_lab_tests(
        self, print_function, local
    ):
        prod_env = fabfile.Env("some_branch")
        fabfile.write_cron_lab_tests(prod_env)
        local.assert_called_once_with("echo '0/5 * * * * ohc \
/home/ohc/.virtualenvs/elcidrfh-some_branch/bin/python \
/usr/lib/ohc/elcidrfh-some_branch/manage.py \
batch_load >> /usr/lib/ohc/log/cron_synch.log 2>&1' | sudo tee \
/etc/cron.d/elcid_batch_test_load")
        print_function.assert_called_once_with(
            'Writing cron elcid_batch_test_load'
        )

    @mock.patch("fabfile.os")
    def test_write_cron_backup(self, os, print_function, local):
        os.path.abspath.return_value = "/somthing/somewhere/fabfile.py"
        prod_env = fabfile.Env("some_branch")
        fabfile.write_cron_backup(prod_env)
        local.assert_called_once_with("echo '0 3 * * * ohc \
/home/ohc/.virtualenvs/elcidrfh-some_branch/bin/fab -f \
/somthing/somewhere/fabfile.py dump_and_copy:some_branch >> \
/usr/lib/ohc/log/cron.log 2>&1' | sudo tee /etc/cron.d/elcid_backup")
        print_function.assert_called_once_with(
            "Writing cron elcid_backup"
        )


@mock.patch("fabfile.print", create=True)
@mock.patch("fabfile.get_private_settings")
@mock.patch("fabfile.run_management_command")
@mock.patch("fabfile.put")
@mock.patch("fabfile.env")
@mock.patch("fabfile.os")
@mock.patch("fabfile.datetime")
class CopyBackupTestCase(FabfileTestCase):
    def test_copy_backup(
        self,
        dt,
        os,
        env,
        put,
        run_management_command,
        get_private_settings,
        print_function
    ):
        get_private_settings.return_value(dict(
            host_string="121.1.1.1",
            remote_passwordpassword="some_password"
        ))
        dt.datetime.now.return_value = datetime.datetime(
            2017, 9, 7
        )
        os.path.isfile.return_value = True
        prod_env = fabfile.Env("some_branch")

        fabfile.copy_backup(prod_env)

        lp = "/usr/lib/ohc/var/back.07.09.2017.elcidrfh_some_branch.sql"
        rp = "/usr/lib/ohc/var/live/back.07.09.2017.elcidrfh_some_branch.sql"
        put.assert_called_once_with(
            local_path=lp,
            remote_path=rp
        )

    def test_copy_backup_no_backup(
        self,
        dt,
        os,
        env,
        put,
        run_management_command,
        get_private_settings,
        print_function
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
            fabfile.copy_backup(self.env)

        self.assertEqual(
            run_management_command.call_args[0][0],
            "error_emailer 'unable to find backup some_backup'"
        )
        print_function.assert_called_once_with("Sending error email")

    def test_put_sends_email(
        self,
        dt,
        os,
        env,
        put,
        run_management_command,
        get_private_settings,
        print_function,
    ):
        get_private_settings.return_value(dict(
            host_string="121.1.1.1",
            password="some_password"
        ))
        put_result = mock.MagicMock()
        put_result.failed = True
        put.return_value = put_result
        with mock.patch(
            "fabfile.Env.backup_name", new_callable=mock.PropertyMock
        ) as prop:
            prop.return_value = "some_backup"
            fabfile.copy_backup(self.env)

        self.assertEqual(
            run_management_command.call_args[0][0],
            "error_emailer 'unable to copy backup some_backup'"
        )
        print_function.assert_called_once_with('Sending error email')


class SendErrorEmailTestCase(FabfileTestCase):
    @mock.patch("fabfile.print", create=True)
    @mock.patch("fabfile.run_management_command")
    def test_send_error_email(self, run_management_command, print_function):
        fabfile.send_error_email("testing", self.env)
        self.assertEqual(
            run_management_command.call_args[0][0],
            "error_emailer 'testing'"
        )
        self.assertEqual(
            run_management_command.call_args[0][1],
            self.env
        )
        print_function.assert_called_once_with('Sending error email')


@mock.patch("fabfile.json")
@mock.patch("fabfile.os")
class GetPrivateSettingsTestCase(unittest.TestCase):
    def test_unable_to_find_file(self, os, json):
        os.path.isfile.return_value = False

        with self.assertRaises(ValueError) as e:
            fabfile.get_private_settings()

        self.assertEqual(
            str(e.exception),
            "unable to find additional settings at \
/usr/lib/ohc/private_settings.json"
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
            "we require 'db_password' in your private settings"
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
            "we require 'additional_settings dict (even if its empty)' in \
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
            "we require 'proxy' in your private settings"
        )

    def test_host_string(self, os, json):
        m = mock.mock_open()
        fab_open = "fabfile.open"
        json.load.return_value = dict(
            db_password="something",
            additional_settings={},
            proxy="127.0.0.1",
            remote_password=None
        )
        with mock.patch(fab_open, m, create=True):
            with self.assertRaises(ValueError) as e:
                fabfile.get_private_settings()

        self.assertEqual(
            str(e.exception),
            "we expect host string to be set, this should be 127.0.0.1 on test, or \
the address you want to sync to on prod in your private settings"
        )

    def test_remote_password(self, os, json):
        m = mock.mock_open()
        fab_open = "fabfile.open"
        json.load.return_value = dict(
            db_password="something",
            additional_settings={},
            proxy="127.0.0.1",
            host_string="some_str"
        )
        with mock.patch(fab_open, m, create=True):
            with self.assertRaises(ValueError) as e:
                fabfile.get_private_settings()

        self.assertEqual(
            str(e.exception),
            "we require 'remote_password' in your private settings"
        )

    def test_get_private_settings(self, os, json):
        m = mock.mock_open()
        fab_open = "fabfile.open"
        expected = dict(
            db_password="something",
            additional_settings={},
            proxy="127.0.0.1",
            host_string="some_str",
            remote_password=None
        )
        json.load.return_value = expected
        with mock.patch(fab_open, m, create=True):
            result = fabfile.get_private_settings()

        self.assertEqual(result, expected)


class DeployTestCase(FabfileTestCase):
    @mock.patch("fabfile.Env")
    @mock.patch("fabfile.get_private_settings")
    @mock.patch("fabfile.get_python_3")
    @mock.patch("fabfile.pip_create_virtual_env")
    @mock.patch("fabfile.pip_create_deployment_env")
    @mock.patch("fabfile.kill_running_processes")
    @mock.patch("fabfile.pip_set_project_directory")
    @mock.patch("fabfile.install_apt_dependencies")
    @mock.patch("fabfile.pip_install_requirements")
    @mock.patch("fabfile.postgres_create_database")
    @mock.patch("fabfile.create_pg_pass")
    @mock.patch("fabfile.postgres_load_database")
    @mock.patch("fabfile.services_symlink_nginx")
    @mock.patch("fabfile.services_symlink_upstart")
    @mock.patch("fabfile.services_create_celery_conf")
    @mock.patch("fabfile.write_cron_lab_tests")
    @mock.patch("fabfile.services_create_local_settings")
    @mock.patch("fabfile.services_create_upstart_conf")
    @mock.patch("fabfile.services_create_gunicorn_conf")
    @mock.patch("fabfile.run_management_command")
    @mock.patch("fabfile.restart_supervisord")
    @mock.patch("fabfile.restart_nginx")
    def test_deploy_no_backup(
        self,
        restart_nginx,
        restart_supervisord,
        run_management_command,
        services_create_gunicorn_conf,
        services_create_upstart_conf,
        services_create_local_settings,
        write_cron_lab_tests,
        services_create_celery_conf,
        services_symlink_upstart,
        services_symlink_nginx,
        postgres_load_database,
        create_pg_pass,
        postgres_create_database,
        pip_install_requirements,
        install_apt_dependencies,
        pip_set_project_directory,
        kill_running_processes,
        pip_create_deployment_env,
        pip_create_virtual_env,
        get_python_3,
        get_private_settings,
        env_constructor,

    ):
        pv = dict(
            proxy="1.2.3",
            host_string="0.0.0.0"
        )
        get_python_3.return_value = "python3"
        get_private_settings.return_value = pv
        env_constructor.return_value = self.env
        fabfile._deploy("some_branch")
        env_constructor.assert_called_once_with(
            "some_branch"
        )
        self.assertTrue(get_private_settings.called)
        get_private_settings.assert_called_once_with()
        self.assertEqual(
            fabfile.env.host_string,
            "0.0.0.0"
        )
        pip_create_virtual_env.assert_called_once_with(
            self.env.virtual_env_path, False, python_path="python3"
        )
        pip_create_deployment_env.assert_called_once_with(
            "some_branch"
        )
        pip_set_project_directory.assert_called_once_with(self.env)
        pip_install_requirements.assert_called_once_with(self.env, "1.2.3")
        install_apt_dependencies.assert_called_once_with()
        kill_running_processes.assert_called_once_with()

        postgres_create_database.assert_called_once_with(self.env, False)
        create_pg_pass.assert_called_once_with(self.env, pv)
        self.assertFalse(postgres_load_database.called)
        services_symlink_nginx.assert_called_once_with(self.env)
        services_symlink_upstart.assert_called_once_with(self.env)
        services_create_local_settings.assert_called_once_with(self.env, pv)
        services_create_gunicorn_conf.assert_called_once_with(self.env)
        services_create_upstart_conf.assert_called_once_with(self.env)
        self.assertEqual(
            run_management_command.call_count, 4
        )
        first_call = run_management_command.call_args_list[0][0]
        self.assertEqual(
            first_call[0], "collectstatic --noinput"
        )

        self.assertEqual(
            first_call[1], self.env
        )

        second_call = run_management_command.call_args_list[1][0]
        self.assertEqual(
            second_call[0], "migrate --noinput"
        )

        self.assertEqual(
            second_call[1], self.env
        )

        third_call = run_management_command.call_args_list[2][0]
        self.assertEqual(
            third_call[0], "create_singletons"
        )

        self.assertEqual(
            third_call[1], self.env
        )

        fourth_call = run_management_command.call_args_list[3][0]
        self.assertEqual(
            fourth_call[0], "load_lookup_lists"
        )

        self.assertEqual(
            fourth_call[1], self.env
        )
        restart_supervisord.assert_called_once_with(self.env)
        restart_nginx.assert_called_once_with()

    @mock.patch("fabfile.os")
    @mock.patch("fabfile.Env")
    @mock.patch("fabfile.get_private_settings")
    @mock.patch("fabfile.get_python_3")
    @mock.patch("fabfile.pip_create_virtual_env")
    @mock.patch("fabfile.pip_create_deployment_env")
    @mock.patch("fabfile.kill_running_processes")
    @mock.patch("fabfile.pip_set_project_directory")
    @mock.patch("fabfile.install_apt_dependencies")
    @mock.patch("fabfile.pip_install_requirements")
    @mock.patch("fabfile.postgres_create_database")
    @mock.patch("fabfile.create_pg_pass")
    @mock.patch("fabfile.postgres_load_database")
    @mock.patch("fabfile.services_symlink_nginx")
    @mock.patch("fabfile.services_symlink_upstart")
    @mock.patch("fabfile.services_create_celery_conf")
    @mock.patch("fabfile.write_cron_lab_tests")
    @mock.patch("fabfile.services_create_local_settings")
    @mock.patch("fabfile.services_create_upstart_conf")
    @mock.patch("fabfile.services_create_gunicorn_conf")
    @mock.patch("fabfile.run_management_command")
    @mock.patch("fabfile.restart_supervisord")
    @mock.patch("fabfile.restart_nginx")
    def test_deploy_backup(
        self,
        restart_nginx,
        restart_supervisord,
        run_management_command,
        services_create_gunicorn_conf,
        services_create_upstart_conf,
        services_create_local_settings,
        write_cron_lab_tests,
        services_create_celery_conf,
        services_symlink_upstart,
        services_symlink_nginx,
        postgres_load_database,
        create_pg_pass,
        postgres_create_database,
        pip_install_requirements,
        install_apt_dependencies,
        pip_set_project_directory,
        kill_running_processes,
        pip_create_deployment_env,
        pip_create_virtual_env,
        get_python_3,
        get_private_settings,
        env_constructor,
        os
    ):
        pv = dict(
            proxy="1.2.3",
            host_string="0.0.0.0"
        )
        get_private_settings.return_value = pv
        get_python_3.return_value = "python3"
        env_constructor.return_value = self.env
        os.path.isfile.return_value = True
        fabfile._deploy("some_branch", "some_backup")

        os.path.isfile.assert_called_once_with("some_backup")
        env_constructor.assert_called_once_with(
            "some_branch"
        )
        self.assertTrue(get_private_settings.called)
        get_private_settings.assert_called_once_with()
        self.assertEqual(
            fabfile.env.host_string,
            "0.0.0.0"
        )
        pip_create_virtual_env.assert_called_once_with(
            self.env.virtual_env_path, False, python_path="python3"
        )
        pip_create_deployment_env.assert_called_once_with("some_branch")
        pip_set_project_directory.assert_called_once_with(self.env)
        pip_install_requirements.assert_called_once_with(
            self.env, "1.2.3"
        )

        postgres_create_database.assert_called_once_with(
            self.env,False
        )
        create_pg_pass.assert_called_once_with(
            self.env, pv
        )
        postgres_load_database.assert_called_once_with(
            "some_backup", self.env
        )
        services_symlink_nginx.assert_called_once_with(self.env)
        services_symlink_upstart.assert_called_once_with(self.env)
        services_create_local_settings.assert_called_once_with(
            self.env, pv
        )
        write_cron_lab_tests.assert_called_once_with(
            self.env
        )
        services_create_gunicorn_conf.assert_called_once_with(self.env)
        services_create_upstart_conf.assert_called_once_with(self.env)
        write_cron_lab_tests.assert_called_once_with(self.env)
        services_create_celery_conf.assert_called_once_with(self.env)
        self.assertEqual(
            run_management_command.call_count, 4
        )
        first_call = run_management_command.call_args_list[0][0]
        self.assertEqual(
            first_call[0], "collectstatic --noinput"
        )

        self.assertEqual(
            first_call[1], self.env
        )

        second_call = run_management_command.call_args_list[1][0]
        self.assertEqual(
            second_call[0], "migrate --noinput"
        )

        self.assertEqual(
            second_call[1], self.env
        )

        third_call = run_management_command.call_args_list[2][0]
        self.assertEqual(
            third_call[0], "create_singletons"
        )

        self.assertEqual(
            third_call[1], self.env
        )

        fourth_call = run_management_command.call_args_list[3][0]
        self.assertEqual(
            fourth_call[0], "load_lookup_lists"
        )

        self.assertEqual(
            fourth_call[1], self.env
        )

        restart_supervisord.assert_called_once_with(self.env)
        restart_nginx.assert_called_once_with()

    @mock.patch("fabfile.os")
    @mock.patch("fabfile.Env")
    @mock.patch("fabfile.get_private_settings")
    @mock.patch("fabfile.pip_create_virtual_env")
    @mock.patch("fabfile.pip_set_project_directory")
    @mock.patch("fabfile.pip_install_requirements")
    @mock.patch("fabfile.postgres_create_database")
    @mock.patch("fabfile.postgres_load_database")
    @mock.patch("fabfile.services_symlink_nginx")
    @mock.patch("fabfile.services_symlink_upstart")
    @mock.patch("fabfile.services_create_local_settings")
    @mock.patch("fabfile.services_create_gunicorn_conf")
    @mock.patch("fabfile.run_management_command")
    @mock.patch("fabfile.restart_supervisord")
    @mock.patch("fabfile.restart_nginx")
    def test_deploy_backup_raises(
        self,
        restart_nginx,
        restart_supervisord,
        run_management_command,
        services_create_gunicorn_conf,
        services_create_local_settings,
        services_symlink_upstart,
        services_symlink_nginx,
        postgres_load_database,
        postgres_create_database,
        pip_install_requirements,
        pip_set_project_directory,
        pip_create_virtual_env,
        get_private_settings,
        env_constructor,
        os
    ):
        # mock everything because if this fails, we don't want it to
        # accidentally run roughshod on our env
        os.path.isfile.return_value = False
        with self.assertRaises(ValueError) as er:
            fabfile._deploy("some_branch", "some_nonexistent_backup")

        self.assertEqual(
            str(er.exception),
            "unable to find backup some_nonexistent_backup"
        )


class DeployTestTestCase(FabfileTestCase):
    @mock.patch("fabfile.infer_current_branch")
    @mock.patch("fabfile.Env")
    @mock.patch("fabfile._deploy")
    @mock.patch("fabfile.run_management_command")
    @mock.patch("fabfile.print", create=True)
    def test_deploy_test(
        self,
        print_function,
        run_management_command,
        deploy,
        env_constructor,
        infer_current_branch
    ):
        infer_current_branch.return_value = "new_branch"
        env_constructor.return_value = self.env
        run_management_command.return_value = "some status"
        fabfile.deploy_test("some_backup")
        deploy.assert_called_once_with(
            "new_branch", "some_backup", remove_existing=True
        )
        env_constructor.assert_called_once_with("new_branch")

        self.assertEqual(
            print_function.call_count, 4
        )
        first_call = print_function.call_args_list[0][0][0]
        self.assertEqual(
            first_call, "=" * 20
        )

        second_call = print_function.call_args_list[1][0][0]
        self.assertEqual(
            second_call, "new environment was"
        )

        third_call = print_function.call_args_list[2][0][0]
        self.assertEqual(
            third_call, "some status"
        )

        fourth_call = print_function.call_args_list[3][0][0]
        self.assertEqual(
            fourth_call, "=" * 20
        )


@mock.patch("fabfile.get_private_settings")
class ValidatePrivateSettingsTestCase(FabfileTestCase):
    def test_error_on_no_host(self, get_private_settings):
        get_private_settings.return_value = dict(password="something")
        with self.assertRaises(ValueError) as er:
            fabfile.validate_private_settings()

        self.assertEqual(
            str(er.exception),
            'we need a host string inorder to scp data to a backup server'
        )

    def test_error_on_no_password(self, get_private_settings):
        get_private_settings.return_value = dict(host_string="something")
        with self.assertRaises(ValueError) as er:
            fabfile.validate_private_settings()

        self.assertEqual(
            str(er.exception),
            'we need the password of the backup server inorder to scp data \
to a backup server'
        )

    def test_no_error_when_valid(self, get_private_settings):
        get_private_settings.return_value = dict(
            host_string="something",
            password="password"
        )


@mock.patch('fabfile.print', create=True)
class DiffStatusTestCase(FabfileTestCase):
    def get_status(self, **kwargs):
        return dict(
            all_time=dict(
                demographics=1
            ),
            last_week=dict(
                demographics=1
            )
        )

    def test_same(self, print_function):
        fabfile.diff_status(
            json.dumps(self.get_status()),
            json.dumps(self.get_status())
        )
        self.assertEqual(print_function.call_count, 4)
        all_calls = print_function.call_args_list
        self.assertEqual(
            all_calls[0][0][0],
            'looking at all_time'
        )

        self.assertEqual(
            all_calls[1][0][0],
            'no difference'
        )

        self.assertEqual(
            all_calls[2][0][0],
            'looking at last_week'
        )

        self.assertEqual(
            all_calls[3][0][0],
            'no difference'
        )

    def test_new_status_new_subrecord(self, print_function):
        new_status = self.get_status()
        new_status["all_time"]["diagnoses"] = 2
        fabfile.diff_status(
            json.dumps(self.get_status()),
            json.dumps(new_status)
        )
        self.assertEqual(print_function.call_count, 4)
        all_calls = print_function.call_args_list
        self.assertEqual(
            all_calls[0][0][0],
            'looking at all_time'
        )

        self.assertEqual(
            all_calls[1][0][0],
            'missing diagnoses from old'
        )

        self.assertEqual(
            all_calls[2][0][0],
            'looking at last_week'
        )

        self.assertEqual(
            all_calls[3][0][0],
            'no difference'
        )

    def test_old_status_new_subrecord(self, print_function):
        old_status = self.get_status()
        old_status["last_week"]["diagnoses"] = 2
        fabfile.diff_status(
            json.dumps(old_status),
            json.dumps(self.get_status())
        )
        self.assertEqual(print_function.call_count, 4)
        all_calls = print_function.call_args_list
        self.assertEqual(
            all_calls[0][0][0],
            'looking at all_time'
        )

        self.assertEqual(
            all_calls[1][0][0],
            'no difference'
        )

        self.assertEqual(
            all_calls[2][0][0],
            'looking at last_week'
        )

        self.assertEqual(
            all_calls[3][0][0],
            'missing diagnoses from new'
        )

    def test_different_amount(self, print_function):
        old_status = self.get_status()
        old_status["all_time"]["demographics"] = 2
        fabfile.diff_status(
            json.dumps(old_status),
            json.dumps(self.get_status())
        )
        self.assertEqual(print_function.call_count, 4)
        all_calls = print_function.call_args_list
        self.assertEqual(
            all_calls[0][0][0],
            'looking at all_time'
        )

        self.assertEqual(
            all_calls[1][0][0],
            'for demographics we used to have 2 but now have 1'
        )

        self.assertEqual(
            all_calls[2][0][0],
            'looking at last_week'
        )

        self.assertEqual(
            all_calls[3][0][0],
            'no difference'
        )


@mock.patch("fabfile.dump_database")
@mock.patch("fabfile.copy_backup")
@mock.patch("fabfile.send_error_email")
class DumpAndCopyTestCase(FabfileTestCase):
    @mock.patch("fabfile.Env")
    def test_error_raised(
        self, Env, send_error_email, copy_backup, dump_database
    ):
        env = Env.return_value
        dump_database.side_effect = ValueError("break")
        fabfile.dump_and_copy("some_env")
        send_error_email.assert_called_once_with(
            "database backup failed with 'break'", env
        )
        self.assertFalse(copy_backup.called)

    @mock.patch("fabfile.Env")
    def test_error_not_raised(
        self, Env, send_error_email, copy_backup, dump_database
    ):
        Env.return_value = self.env
        fabfile.dump_and_copy("some_env")
        dump_database.assert_called_once_with(
            self.env, self.env.database_name, self.env.backup_name
        )
        copy_backup.assert_called_once_with(self.env)


@mock.patch("fabfile.is_load_running")
@mock.patch("fabfile.local")
@mock.patch("fabfile.time")
@mock.patch("fabfile.datetime")
@mock.patch("fabfile.os")
@mock.patch("fabfile.print", create=True)
class DumpDatabaseTestCase(FabfileTestCase):
    def test_status_found(
        self, print_fun, os, dt, time, local, is_load_running
    ):
        is_load_running.return_value = None
        os.path.return_value = True
        fabfile.dump_database(self.env, "db_name", "backup_name")
        self.assertEqual(is_load_running.call_count, 1)
        self.assertFalse(time.sleep.called)
        local.assert_called_once_with(
            "pg_dump db_name -U ohc > backup_name"
        )

    def test_timed_out(
        self, print_fun, os, dt, time, local, is_load_running
    ):
        is_load_running.return_value = True
        os.path.return_value = True
        first_call = datetime.datetime.now()
        second_call = first_call + datetime.timedelta(seconds=3640)
        dt.datetime.now.side_effect = [first_call, second_call]
        with self.assertRaises(fabfile.FabException) as fe:
            fabfile.dump_database(self.env, "db_name", "backup_name")
        self.assertEqual(
            str(fe.exception),
            "Database synch failed as it has been running for > an hour"
        )

    def test_fails_first_time_works_the_next(
        self, print_fun, os, dt, time, local, is_load_running
    ):
        dt.datetime.now.return_value = datetime.datetime.now()
        is_load_running.side_effect = [True, None]
        os.path.return_value = True
        fabfile.dump_database(self.env, "db_name", "backup_name")

        print_fun.assert_called_once_with(
            "One or more loads are currently running, sleeping for 30 secs"
        )
        time.sleep.assert_called_once_with(30)

        local.assert_called_once_with(
            "pg_dump db_name -U ohc > backup_name"
        )

    def no_cron_job(
        self, print_fun, os, dt, time, local, is_load_running
    ):
        os.path.return_value = False
        fabfile.dump_database("db_name", "backup_name")
        self.assertFalse(is_load_running.called)
        self.assertFalse(time.called)
        self.assertFalse(dt.called)
        local.assert_called_once_with(
            "pg_dump db_name -U ohc > backup_name"
        )


class DeployProdTestCase(FabfileTestCase):
    @mock.patch("fabfile.diff_status")
    @mock.patch("fabfile.infer_current_branch")
    @mock.patch("fabfile.datetime")
    @mock.patch("fabfile.Env")
    @mock.patch("fabfile.validate_private_settings")
    @mock.patch("fabfile.local")
    @mock.patch("fabfile.write_cron_backup")
    @mock.patch("fabfile.dump_database")
    @mock.patch("fabfile.run_management_command")
    @mock.patch("fabfile._deploy")
    @mock.patch("fabfile.print", create=True)
    def test_deploy_prod(
        self,
        print_function,
        _deploy,
        run_management_command,
        dump_database,
        write_cron_backup,
        local,
        validate_private_settings,
        env_constructor,
        dt,
        infer_current_branch,
        diff_status
    ):
        infer_current_branch.return_value = "new_branch"
        dt.datetime.now.return_value = datetime.datetime(
            2017, 9, 8, 10, 47
        )
        old_env = Env("old_env")
        new_env = Env("new_env")
        env_constructor.side_effect = [old_env, new_env]
        run_management_command.side_effect = [
            "old_status", "new_status"
        ]
        fabfile.deploy_prod("new_branch")
        validate_private_settings.assert_called_once_with()

        dump_database.assert_called_once_with(
            old_env,
            'elcidrfh_old_env',
            "/usr/lib/ohc/var/release.08.09.2017.10.47.elcidrfh_old_env.sql"
        )

        write_cron_backup.assert_called_once_with(new_env)
        _deploy.assert_called_once_with(
            "new_branch",
            '/usr/lib/ohc/var/release.08.09.2017.10.47.elcidrfh_old_env.sql',
            remove_existing=False
        )
        self.assertEqual(
            run_management_command.call_count, 2
        )
        first_call = run_management_command.call_args_list[0][0]
        self.assertEqual(
            first_call, ("status_report", old_env,)
        )

        second_call = run_management_command.call_args_list[1][0]
        self.assertEqual(
            second_call, ("status_report", new_env,)
        )

        self.assertEqual(
            print_function.call_count, 0
        )

        diff_status.assert_called_once_with("new_status", "old_status")

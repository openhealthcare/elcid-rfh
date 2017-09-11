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
from fabfile import Env


@mock.patch("fabfile.local")
class CloneBranchTestCase(OpalTestCase):
    def test_clone_branch(self, local):
        branch_name = "some-branch"
        expected = "git clone -b some-branch \
https://github.com/openhealthcare/elcid-rfh \
/usr/lib/ohc/elcidrfh-some-branch"
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
        m.assert_called_once_with('/usr/lib/ohc/private_settings.json', 'w')


class FabfileTestCase(OpalTestCase):
    def setUp(self):
        self.env = fabfile.Env("some_branch")


class EnvTestCase(FabfileTestCase):
    def test_project_directory(self):
        self.assertEqual(
            self.env.project_directory,
            "/usr/lib/ohc/elcidrfh-some_branch"
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
            "/usr/lib/ohc/var/back.07.09.2017.elcidrfh_some_branch.sql"
        )
        self.assertTrue(dt.datetime.now.called)

    @mock.patch("fabfile.datetime")
    def test_release_backup_name(self, dt):
        dt.datetime.now.return_value = datetime.datetime(
            2017, 9, 7, 11, 12
        )
        self.assertEqual(
            self.env.release_backup_name,
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
class RunManagementCommandTestCase(FabfileTestCase):
    def test_run_management_command(self, lcd, local):
        local.return_value = "something"
        result = fabfile.run_management_command("some_command", self.env)
        local.called_once_with("as")
        self.assertEqual(result, "something")
        lcd.assert_called_once_with("/usr/lib/ohc/elcidrfh-some_branch")


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
--upgrade pip --proxy some_proxy"
        )
        second_call = local.call_args_list[1][0][0]
        self.assertEqual(
            second_call,
            "/home/ohc/.virtualenvs/elcidrfh-some_branch/bin/pip install -r \
requirements.txt --proxy some_proxy"
        )

    def test_set_project_directory(self, local):
        fabfile.pip_set_project_directory(self.env)
        local.assert_called_once_with(
            "echo '/usr/lib/ohc/elcidrfh-some_branch' > \
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
/usr/lib/ohc/elcidrfh-some_branch/etc/nginx.conf"
        )

        os.path.isfile.assert_called_once_with(
            "/usr/lib/ohc/elcidrfh-some_branch/etc/nginx.conf"
        )

    @mock.patch('fabfile.local')
    @mock.patch('fabfile.os')
    def test_services_symlink_nginx_if_exists(self, os, local):
        os.path.isfile.return_value = True
        fabfile.services_symlink_nginx(self.env)

        os.path.isfile.assert_called_once_with(
            "/usr/lib/ohc/elcidrfh-some_branch/etc/nginx.conf"
        )
        first_call = local.call_args_list[0][0][0]
        self.assertEqual(
            first_call,
            "sudo rm /etc/nginx/sites-enabled/elcidrfh-some_branch"
        )

        second = local.call_args_list[1][0][0]
        self.assertEqual(
            second,
            "sudo ln -s /usr/lib/ohc/elcidrfh-some_branch/etc/nginx.conf \
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
/usr/lib/ohc/elcidrfh-some_branch/etc/upstart.conf"
        )

        os.path.isfile.assert_called_once_with(
            "/usr/lib/ohc/elcidrfh-some_branch/etc/upstart.conf"
        )

    @mock.patch('fabfile.local')
    @mock.patch('fabfile.os')
    def test_services_symlink_upstart_if_exists(self, os, local):
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
> /usr/lib/ohc/var/back.$(date +"%d.%m.%Y").elcidrfh_some_branch.sql\' | \
sudo tee /etc/cron.d/elcid_backup')

    @mock.patch("fabfile.os")
    def test_cron_copy_backup(self, os, local):
        os.path.abspath.return_value = "/somthing/somewhere/fabfile.py"
        fabfile.cron_copy_backup(self.env)
        local.assert_called_once_with("echo '0 2 * * * ohc \
/home/ohc/.virtualenvs/elcidrfh-some_branch/bin/fab -f \
/somthing/somewhere/fabfile.py \
copy_backup:elcidrfh_some_branch' | sudo tee /etc/cron.d/elcid_copy")
        self.assertTrue(os.path.abspath)


@mock.patch("fabfile.get_private_settings")
@mock.patch("fabfile.run_management_command")
@mock.patch("fabfile.put")
@mock.patch("fabfile.env")
@mock.patch("fabfile.os")
@mock.patch("fabfile.datetime")
class CopyBackupTestCase(FabfileTestCase):
    def test_copy_backup(
        self, dt, os, env, put, run_management_command, get_private_settings
    ):
        get_private_settings.return_value(dict(
            host_string="121.1.1.1",
            password="some_password"
        ))
        dt.datetime.now.return_value = datetime.datetime(
            2017, 9, 7
        )
        os.path.isfile.return_value = True
        fabfile.copy_backup(self.env.branch)
        p = "/usr/lib/ohc/var/back.07.09.2017.elcidrfh_some_branch.sql"
        put.assert_called_once_with(
            local_path=p,
            remote_path=p
        )

    def test_copy_backup_no_backup(
        self, dt, os, env, put, run_management_command, get_private_settings
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
        self, dt, os, env, put, run_management_command, get_private_settings
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


class DeployTestCase(FabfileTestCase):
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
    @mock.patch("fabfile.services_create_gunicorn_settings")
    @mock.patch("fabfile.run_management_command")
    def test_deploy_no_backup(
        self,
        run_management_command,
        services_create_gunicorn_settings,
        services_create_local_settings,
        services_symlink_upstart,
        services_symlink_nginx,
        postgres_load_database,
        postgres_create_database,
        pip_install_requirements,
        pip_set_project_directory,
        pip_create_virtual_env,
        get_private_settings,
        env_constructor
    ):
        pv = dict(
            proxy="1.2.3",
            host_string="0.0.0.0"
        )
        get_private_settings.return_value = pv
        env_constructor.return_value = self.env
        fabfile._deploy("some_branch")
        env_constructor.assert_called_once_with("some_branch")
        self.assertTrue(get_private_settings.called)
        get_private_settings.assert_called_once_with()
        self.assertEqual(
            fabfile.env.host_string,
            "0.0.0.0"
        )
        pip_create_virtual_env.assert_called_once_with(self.env)
        pip_set_project_directory.assert_called_once_with(self.env)
        pip_install_requirements.assert_called_once_with(self.env, "1.2.3")

        postgres_create_database.assert_called_once_with(self.env)
        self.assertFalse(postgres_load_database.called)
        services_symlink_nginx.assert_called_once_with(self.env)
        services_symlink_upstart.assert_called_once_with(self.env)
        services_create_local_settings.assert_called_once_with(self.env, pv)
        services_create_gunicorn_settings.assert_called_once_with(self.env)
        self.assertEqual(
            run_management_command.call_count, 3
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
            second_call[0], "migrate"
        )

        self.assertEqual(
            second_call[1], self.env
        )

        third_call = run_management_command.call_args_list[2][0]
        self.assertEqual(
            third_call[0], "load_lookup_lists"
        )

        self.assertEqual(
            third_call[1], self.env
        )

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
    @mock.patch("fabfile.services_create_gunicorn_settings")
    @mock.patch("fabfile.run_management_command")
    def test_deploy_backup(
        self,
        run_management_command,
        services_create_gunicorn_settings,
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
        pv = dict(
            proxy="1.2.3",
            host_string="0.0.0.0"
        )
        get_private_settings.return_value = pv
        env_constructor.return_value = self.env
        os.path.isfile.return_value = True
        fabfile._deploy("some_branch", "some_backup")

        os.path.isfile.assert_called_once_with("some_backup")
        env_constructor.assert_called_once_with("some_branch")
        self.assertTrue(get_private_settings.called)
        get_private_settings.assert_called_once_with()
        self.assertEqual(
            fabfile.env.host_string,
            "0.0.0.0"
        )
        pip_create_virtual_env.assert_called_once_with(self.env)
        pip_set_project_directory.assert_called_once_with(self.env)
        pip_install_requirements.assert_called_once_with(self.env, "1.2.3")

        postgres_create_database.assert_called_once_with(self.env)
        postgres_load_database.assert_called_once_with("some_backup", self.env)
        services_symlink_nginx.assert_called_once_with(self.env)
        services_symlink_upstart.assert_called_once_with(self.env)
        services_create_local_settings.assert_called_once_with(self.env, pv)
        services_create_gunicorn_settings.assert_called_once_with(self.env)
        self.assertEqual(
            run_management_command.call_count, 3
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
            second_call[0], "migrate"
        )

        self.assertEqual(
            second_call[1], self.env
        )

        third_call = run_management_command.call_args_list[2][0]
        self.assertEqual(
            third_call[0], "load_lookup_lists"
        )

        self.assertEqual(
            third_call[1], self.env
        )

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
    @mock.patch("fabfile.services_create_gunicorn_settings")
    @mock.patch("fabfile.run_management_command")
    def test_deploy_backup_raises(
        self,
        run_management_command,
        services_create_gunicorn_settings,
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
        deploy.assert_called_once_with("new_branch", "some_backup")
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


class DeployProdTestCase(FabfileTestCase):
    @mock.patch("fabfile.infer_current_branch")
    @mock.patch("fabfile.datetime")
    @mock.patch("fabfile.Env")
    @mock.patch("fabfile.validate_private_settings")
    @mock.patch("fabfile.local")
    @mock.patch("fabfile.cron_write_backup")
    @mock.patch("fabfile.cron_copy_backup")
    @mock.patch("fabfile.run_management_command")
    @mock.patch("fabfile._deploy")
    @mock.patch("fabfile.print", create=True)
    def test_deploy_prod(
        self,
        print_function,
        _deploy,
        run_management_command,
        cron_copy_backup,
        cron_write_backup,
        local,
        validate_private_settings,
        env_constructor,
        dt,
        infer_current_branch
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
        local.assert_called_once_with(
            "sudo -u postgres pg_dump elcidrfh_old_env -U postgres > \
/usr/lib/ohc/var/release.08.09.2017.10.47.elcidrfh_old_env.sql"
        )
        cron_write_backup.assert_called_once_with(new_env)
        cron_copy_backup.assert_called_once_with(new_env)
        _deploy.assert_called_once_with(
            new_env, old_env.backup_name
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
            print_function.call_count, 7
        )

        self.assertEqual(
            print_function.call_args_list[0][0][0],
            "=" * 20
        )

        self.assertEqual(
            print_function.call_args_list[1][0][0],
            "old environment was"
        )

        self.assertEqual(
            print_function.call_args_list[2][0][0],
            "old_status"
        )

        self.assertEqual(
            print_function.call_args_list[3][0][0],
            "=" * 20
        )

        self.assertEqual(
            print_function.call_args_list[4][0][0],
            "new environment was"
        )

        self.assertEqual(
            print_function.call_args_list[5][0][0],
            "new_status"
        )

        self.assertEqual(
            print_function.call_args_list[6][0][0],
            "=" * 20
        )

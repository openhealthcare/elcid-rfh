"""
This deals with deployment for the rfh.

Before you being make sure that in ../private_settings.json
you have
    1) a db_user
    2) a db_password
    3) an empty dictionary called additional_settings or a dictionary
       of any other variables you want set in your local settings

2 big tasks to look at

deploy_test, this takes the name of

deploy_prod, this will take a database back up and load it in and set up the
cron jobs to copy it over

"""

import datetime
import json
import copy
from jinja2 import Environment, FileSystemLoader
from fabric.api import local, env, settings, hide
from fabric.context_managers import lcd
from fabric.contrib.files import _expand_path
from fabric.operations import put
from ..secure.secure_settings import PROXY
import os.path

UNIX_USER = "ohc"
DB_USER = "ohc"
RELEASE_NAME = "elcidrfh-{branch}"
VIRTUAL_ENV_PATH = "/{usr}/.virtualenvs/{release_name}"
PROJECT_DIRECTORY = "/usr/local/ohc/{release_name}"
BACKUP_NAME = "/usr/local/ohc/var/back.{dt}.{db_name}.sql"
MODULE_NAME = "elcid"
CRON_COMMENT = "{} back up".format(MODULE_NAME)
DB_COMMAND_PREFIX = "sudo -u postgres psql --command"
TEMPLATE_DIR = os.path.abspath(os.path.dirname(__file__))

PRIVATE_SETTINGS = "../private_settings.json"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


class Env(object):
    def __init__(self, branch):
        self.branch = branch

    @property
    def release_name(self):
        return RELEASE_NAME.format(branch=self.branch_name)

    @property
    def virtual_env_path(self):
        return VIRTUAL_ENV_PATH.format(
            usr=UNIX_USER,
            release_name=self.release_name
        )

    @property
    def project_directory(self):
        return PROJECT_DIRECTORY.format(
            release_name=self.release_name
        )

    @property
    def database_name(self):
        return self.release_name.replace("-", "").replace(".", "")

    @property
    def backup_name(self):
        now = datetime.now()
        return BACKUP_NAME.format(
            dt=now.strftime("%d.%m.%Y"),
            db_name=self.database_name
        )


def run_management_command(some_command, env):
    with lcd(env.project_directory):
        cmd = "{0}/bin/python manage.py {1}".format(
            env.virtual_env_path, some_command
        )
        result = local(cmd, capture=True)

    return result


def lexists(path):
    """
        checks if a file exists
    """
    with settings(hide('everything'), warn_only=True):
        return not local('test -e {}'.format(_expand_path(path))).failed


def pip_create_virtual_env(new_env):
    if not lexists(new_env.virtual_env_path):
        local("/usr/bin/virtualenv {}".format(new_env.virtual_env_path))
    return


def pip_install_requirements(new_env):
    pip = "{}/bin/pip".format(new_env.virtual_env_path)
    local("{0} install --proxy {1} requirements.txt".format(pip, PROXY))


def pip_set_project_directory(some_env):
    local("echo '{0}' > {1}/.project".format(
        some_env.release_name, some_env.virtual_env_path
    ))

    def install_requirements(cls):
        if env.http_proxy:
            local("{0} install -r requirements.txt --proxy {1}".format(
                cls.get_pip(), env.http_proxy
            ))
        else:
            local("{0} install -r requirements.txt".format(cls.get_pip()))


def postgres_command(command, capture=False):
    return local('{0} "{1}"'.format(DB_COMMAND_PREFIX, command), capture=capture)


def postgres_create_database(some_env):
    """ creates a database and user if they don't already exist.
        the db_name is created from the release name
    """

    #  https://stackoverflow.com/questions/14549270/check-if-database-exists-in-postgresql-using-shell
    command = "sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw {database_name} | wc -l"
    database_doesnt_exist = "0" in local(
        command.format(database_name=some_env.database_name)
    )

    if database_doesnt_exist:
        postgres_command("CREATE DATABASE {0}".format(env.db_name))
        postgres_command("GRANT ALL PRIVILEGES ON DATABASE {0} TO {1}".format(
            some_env.database_name, DB_USER
        ))


def postgres_load_database(backup_name, new_env):
    # check that the database isn't empty
    # check that the database dump has been taken within the last hour

    # so lets talk this through we should never load in data when there
    # is already data.
    # we should load data in
    cmd = 'sudo -u postgres psql {database_name}" -c "select count(*) from pg_class c join pg_namespace s on s.oid = c.relnamespace"'
    cmd = cmd + ' where s.nspname not in (\'pg_catalog\', \'information_schema\') and s.nspname not like \'pg_temp%\')'

    not_populated = "0" in postgres_command(
        cmd, capture=True
    )

    if not_populated:
        if not lexists(backup_name):
            raise ValueError("unable to find a backup at {}".format(
                backup_name)
            )

        modified_unix_ts = os.path.getmttime(backup_name)
        modified_dt = datetime.fromtimestamp(modified_unix_ts)
        an_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)

        if modified_dt < an_hour_ago:
            raise ValueError(
                "the latest back up is too old, its from %s" % (
                    modified_dt
                )
            )

        local("sudo -u postgres psql -d {0} -f {1}".format(
            new_env.database_name,
            backup_name
        ))
    else:
        print 'Not populating {} as its already populated'.format(
            new_env.database_name
        )


def services_symlink_nginx(new_env):
    absPathNginxConf = os.path.join(
        new_env.project_directory, "etc/nginx.conf"
    )
    if not lexists(absPathNginxConf):
        raise ValueError("we expect an nginx conf to exist")

    symlink_name = '/etc/nginx/sites-enabled/{}'.format(new_env.release_name)
    if lexists(symlink_name):
        local("sudo rm {}".format(symlink_name))

    local('sudo ln -s {0} {1}'.format(absPathNginxConf, symlink_name))


def services_symlink_upstart(new_env):
    absPathUpstartConf = os.path.join(
        new_env.project_directory, "etc/upstart.conf"
    )
    if not lexists(absPathUpstartConf):
        raise ValueError("we expect an upstart conf to exist")

    symlink_name = '/etc/init/{}.conf'.format(env.project_name)
    if lexists(symlink_name):
        local("sudo rm {}".format(symlink_name))

    local('sudo ln -s {0} {1}'.format(absPathUpstartConf, symlink_name))


def services_create_local_settings(new_env, additional_settings):
    new_settings = copy.copy(additional_settings)
    new_settings["db_name"] = new_env.database_name
    template = jinja_env.get_template(
        'conf_templates/local_settings.py.jinja2'
    )
    output = template.render(new_settings)
    local_settings_file = '{0}/{1}/local_settings.py'.format(
        new_env.project_directory, MODULE_NAME
    )

    if not lexists(local_settings_file):
        with open(local_settings_file, 'w+') as f:
            f.write(output)


def services_create_gunicorn_settings(new_env):
    template = jinja_env.get_template('conf_templates/gunicorn.conf.jinja2')
    output = template.render(
        env_name=new_env.virtual_env_path
    )

    with open("etc/gunicorn.conf", 'w') as f:
        f.write(output)


def restart_supervisord(new_env):
    local("{0}/bin/supervisorctl -c etc/supervisord.conf restart all".format(
        new_env.virtual_env_path
    ))


def restart_nginx():
    local('sudo /etc/init.d/nginx restart')


def cron_write_backup(new_env):
    """ Creates a cron job that has a postgres user writing to a file
    """
    template = jinja_env.get_template('conf_templates/cron_postgres.jinja2')
    output = template.render(
        database_name=new_env.database_name
    )
    with open("/etc/cron.d/{}_backup".format(MODULE_NAME), 'w') as f:
        f.write(output)


def cron_copy_backup(new_env):
    """ Creates a cron job that copies a file to a remote server
    """
    template = jinja_env.get_template('conf_templates/cron_ohc.jinja2')
    fabfile = os.path.dirname(__file__)
    output = template.render(
        fabric_file=fabfile,
        database_name=new_env.database_name
    )
    with open("/etc/cron.d/{}_copy".format(MODULE_NAME), 'w') as f:
        f.write(output)


def copy_backup(branch_name):
    current_env = Env(branch_name)

    if not lexists(current_env.backup_name):
        run_management_command(
            "send error 'unable to find backup {}'".format(
                current_env.backup_name
            )
        )

    try:
        put(
            local_path=current_env.backup_name,
            remote_path=current_env.backup_name
        )
    except:
        run_management_command(
            "send error 'unable to copy backup {}'".format(
                current_env.backup_name
            )
        )


def get_private_settings():
    if not lexists(PRIVATE_SETTINGS):
        raise ValueError(
            "unable to find additional settings at {}".format(
                PRIVATE_SETTINGS
            )
        )

    with open("../private_settings.json") as privado:
        result = json.load(privado)
        if "db_user" not in result:
            raise ValueError('we require a db user ')
        if "db_password" not in result:
            raise ValueError('we require a db password')
        if "additional_settings" not in result:
            e = """
            we require a dictionary of additional_settings (even if its empty)
            """.strip()
            raise ValueError(e)

    return result


def create_empty_env(new_branch):
    # creates an environment with an empty database
    new_env = Env(new_branch)

    # the private settings
    private_settings = get_private_settings()

    # Setup environment
    pip_create_virtual_env(new_env)
    pip_set_project_directory(new_env)
    pip_install_requirements(new_env)

    # create a database
    postgres_create_database(new_env)

    # symlink the nginx conf
    services_symlink_nginx(new_env)

    # symlink the upstart conf
    services_symlink_upstart(new_env)

    # create the local settings used by the django app
    services_create_local_settings(new_env, private_settings)

    services_create_gunicorn_settings(new_env)

    # django setup
    run_management_command("collect_static", new_env)
    run_management_command("migrate", new_env)
    run_management_command("load_lookup_lists", new_env)


def deploy_test(old_branch, new_branch, backup_name=None):
    # the old env that is currently live
    old_env = Env(old_branch)

    if backup_name is None:
        backup_name = old_env.backup_name

    if not lexists(backup_name):
        raise ValueError("unable to find backup {}".format(backup_name))

    # the new env that is going to be live
    new_env = Env(new_branch)

    # the private settings
    private_settings = get_private_settings()

    # Measure old environment
    old_status = run_management_command("status_report", old_env)

    # Setup environment
    pip_create_virtual_env(new_env)
    pip_set_project_directory(new_env)
    pip_install_requirements(new_env)

    # create a database
    postgres_create_database(new_env)

    # load in a backup
    postgres_load_database(backup_name, new_env)

    # symlink the nginx conf
    services_symlink_nginx(new_env)

    # symlink the upstart conf
    services_symlink_upstart(new_env)

    # create the local settings used by the django app
    services_create_local_settings(new_env, private_settings)

    services_create_gunicorn_settings(new_env)

    # django setup
    run_management_command("collect_static", new_env)
    run_management_command("migrate", new_env)
    run_management_command("load_lookup_lists", new_env)
    new_status = run_management_command("status_report", new_env)

    print "=" * 20
    print "old environment was"
    old_status
    print "=" * 20
    print "old environment was"
    new_status
    print "=" * 20


def deploy_prod(new_branch, old_branch):
    old_env = Env(old_branch)
    new_env = Env(new_branch)

    backup_name = "/usr/local/ohc/var/release.{dt}.{db_name}.sql".format(
        dt=datetime.now().strftime("%d.%m.%Y.%H.%M"),
        db_name=old_env.database_name
    )

    dump_str = "pg_dump -d {0} -U postgres > {2}"
    local(dump_str.format(old_env.database_name, backup_name))

    deploy_test(new_branch, old_branch)
    cron_write_backup(new_env)
    cron_copy_backup(new_env)

"""
This deals with deployment for the rfh.

Before you being make sure that in ../private_settings.json
you have
    1) the proxy address
    2) a db_password
    3) an empty dictionary called additional_settings or a dictionary
       of any other variables you want set in your local settings

Make sure the you have a back up directory which is read writeable
that is at BACKUP_DIR

Make sure you have a deployment env that has fabric available

e.g.
workon elcid-deployment or another environment
fab clone_branch your-branch
cd /usr/lib/ohc/elcidrfh-{your branch name}

Then 2 choices

deploy_test, this takes the back up file and name of the new branch.
the back up file will be loaded the environment a database back up from

deploy_prod, this takes the old env and the new env

2 small tasks to look at
create_private_settings will create an empty private settings file in
the appropriate place with the fields for you to fill in

create_empty_env, takes in an environment name
creates you an empty database and a virtual env

The code is in
/usr/lib/ohc/log

The log environment for this project is considered to be
/usr/lib/ohc/log/

The backups are stored in
/usr/lib/ohc/var/

"""
from __future__ import print_function
import datetime
import json
import copy
from jinja2 import Environment, FileSystemLoader
from fabric.api import local, env
from fabric.operations import put
from fabric.context_managers import lcd, settings
from fabric.decorators import task
import os.path

env.hosts = ['127.0.0.1']
UNIX_USER = "ohc"
DB_USER = "ohc"
RELEASE_NAME = "elcidrfh-{branch}"

VIRTUAL_ENV_PATH = "/home/{usr}/.virtualenvs/{release_name}"
PROJECT_ROOT = "/usr/lib/{unix_user}".format(unix_user=UNIX_USER)
PROJECT_DIRECTORY = "{project_root}/{release_name}"
BACKUP_DIR = "{project_root}/var".format(project_root=PROJECT_ROOT)
GIT_URL = "https://github.com/openhealthcare/elcid-rfh"

# the daily back up
BACKUP_NAME = "{backup_dir}/back.{dt}.{db_name}.sql"

# the release back up is take just before the release, and then restored
RELEASE_BACKUP_NAME = "{backup_dir}/release.{dt}.{db_name}.sql"

MODULE_NAME = "elcid"
PROJECT_NAME = MODULE_NAME
CRON_COMMENT = "{} back up".format(MODULE_NAME)
DB_COMMAND_PREFIX = "sudo -u postgres psql --command"
TEMPLATE_DIR = os.path.abspath(os.path.dirname(__file__))
PRIVATE_SETTINGS = "{project_root}/private_settings.json".format(
    project_root=PROJECT_ROOT
)
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


class Env(object):
    def __init__(self, branch):
        self.branch = branch

    @property
    def project_directory(self):
        return PROJECT_DIRECTORY.format(
            project_root=PROJECT_ROOT,
            release_name=self.release_name,
        )

    @property
    def release_name(self):
        return RELEASE_NAME.format(branch=self.branch)

    @property
    def virtual_env_path(self):
        return VIRTUAL_ENV_PATH.format(
            usr=UNIX_USER,
            release_name=self.release_name
        )

    @property
    def database_name(self):
        return self.release_name.replace("-", "_").replace(".", "")

    @property
    def backup_name(self):
        now = datetime.datetime.now()
        return BACKUP_NAME.format(
            backup_dir=BACKUP_DIR,
            dt=now.strftime("%d.%m.%Y"),
            db_name=self.database_name
        )

    @property
    def release_backup_name(self):
        return RELEASE_BACKUP_NAME.format(
            backup_dir=BACKUP_DIR,
            dt=datetime.datetime.now().strftime("%d.%m.%Y.%H.%M"),
            db_name=self.database_name
        )


def run_management_command(some_command, env):
    with lcd(env.project_directory):
        cmd = "{0}/bin/python manage.py {1}".format(
            env.virtual_env_path, some_command
        )
        result = local(cmd, capture=True)
    return result


def pip_create_virtual_env(new_env):
    local("rm -rf {}".format(new_env.virtual_env_path))
    local("/usr/bin/virtualenv {}".format(new_env.virtual_env_path))
    return


def pip_install_requirements(new_env, proxy):
    pip = "{}/bin/pip".format(new_env.virtual_env_path)
    local("{0} install --upgrade pip --proxy {1}".format(pip, proxy))
    local("{0} install -r requirements.txt --proxy {1}".format(pip, proxy))


def pip_set_project_directory(some_env):
    local("echo '{0}' > {1}/.project".format(
        some_env.project_directory, some_env.virtual_env_path
    ))


def postgres_command(command, capture=False):
    return local(
        '{0} "{1}"'.format(DB_COMMAND_PREFIX, command),
        capture=capture
    )


def postgres_create_database(some_env):
    """ creates a database and user if they don't already exist.
        the db_name is created from the release name
    """

    #  https://stackoverflow.com/questions/14549270/check-if-database-exists-in-postgresql-using-shell
    command = "sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -w {database_name} | wc -l"
    database_exists = "0" not in local(
        command.format(database_name=some_env.database_name), capture=True
    )

    if database_exists:
        postgres_command("DROP DATABASE {0}".format(some_env.database_name))

    postgres_command("CREATE DATABASE {0}".format(some_env.database_name))
    postgres_command("GRANT ALL PRIVILEGES ON DATABASE {0} TO {1}".format(
        some_env.database_name, DB_USER
    ))


def postgres_load_database(backup_name, new_env):
    if not os.path.isfile(backup_name):
        raise ValueError("unable to find a backup at {}".format(
            backup_name)
        )

    local("sudo -u postgres psql -d {0} -f {1}".format(
        new_env.database_name,
        backup_name
    ))


def services_symlink_nginx(new_env):
    abs_address = "{}/etc/nginx.conf".format(new_env.project_directory, "")
    if not os.path.isfile(abs_address):
        raise ValueError(
            "we expect an nginx conf to exist at {}".format(abs_address)
        )

    symlink_name = '/etc/nginx/sites-enabled/{}'.format(MODULE_NAME)
    if os.path.islink(symlink_name):
        local("sudo rm {}".format(symlink_name))

    local('sudo ln -s {0} {1}'.format(abs_address, symlink_name))


def services_symlink_upstart(new_env):
    abs_address = "{}/etc/upstart.conf".format(new_env.project_directory, "")
    if not os.path.isfile(abs_address):
        raise ValueError(
            "we expect an upstart conf to exist {}".format(abs_address)
        )
    symlink_name = '/etc/init/{}.conf'.format(PROJECT_NAME)
    local("sudo rm -f {}".format(symlink_name))

    local('sudo ln -s {0} {1}'.format(
        abs_address,
        symlink_name
    ))


def services_create_local_settings(new_env, additional_settings):
    new_settings = copy.copy(additional_settings)
    new_settings["db_name"] = new_env.database_name
    new_settings["db_user"] = DB_USER
    template = jinja_env.get_template(
        'conf_templates/local_settings.py.jinja2'
    )
    output = template.render(new_settings)
    local_settings_file = '{0}/{1}/local_settings.py'.format(
        new_env.project_directory, MODULE_NAME
    )

    local("rm -f {}".format(local_settings_file))

    with open(local_settings_file, 'w') as f:
        f.write(output)


def services_create_gunicorn_conf(new_env):
    template = jinja_env.get_template('conf_templates/gunicorn.conf.jinja2')
    output = template.render(
        env_name=new_env.virtual_env_path
    )
    gunicorn_conf = '{0}/etc/gunicorn.conf'.format(
        new_env.project_directory
    )

    local("rm -f {}".format(gunicorn_conf))

    with open(gunicorn_conf, 'w') as f:
        f.write(output)


def services_create_upstart_conf(new_env):
    template = jinja_env.get_template('conf_templates/upstart.conf.jinja2')
    output = template.render(
        env_name=new_env.virtual_env_path,
        project_directory=new_env.project_directory
    )
    upstart_conf = '{0}/etc/upstart.conf'.format(
        new_env.project_directory
    )

    local("rm -f {}".format(upstart_conf))

    with open(upstart_conf, 'w') as f:
        f.write(output)


def restart_supervisord(new_env):
    local("pkill super; pkill gunic")
    # don't restart supervisorctl as we need to be running the correct
    # supervisord
    local("{0}/bin/supervisord -c {1}/etc/supervisord.conf restart all".format(
        new_env.virtual_env_path, new_env.project_directory
    ))


def restart_nginx():
    local('sudo /etc/init.d/nginx restart')


def cron_write_backup(new_env):
    """ Creates a cron job that has a postgres user writing to a file
    """
    template = jinja_env.get_template('conf_templates/cron_backup.jinja2')
    output = template.render(
        database_name=new_env.database_name,
        backup_dir=BACKUP_DIR
    )

    cron_file = "/etc/cron.d/{0}_backup".format(PROJECT_NAME)
    local("echo '{0}' | sudo tee {1}".format(
        output, cron_file
    ))


def cron_copy_backup(new_env):
    """ Creates a cron job that copies a file to a remote server
    """
    template = jinja_env.get_template('conf_templates/cron_copy.jinja2')
    fabfile = os.path.abspath(__file__).rstrip("c")  # pycs won't cut it
    output = template.render(
        fabric_file=fabfile,
        virtualenv=new_env.virtual_env_path,
        branch=new_env.branch,
        unix_user=UNIX_USER
    )
    cron_file = "/etc/cron.d/{0}_copy".format(PROJECT_NAME)
    local("echo '{0}' | sudo tee {1}".format(
        output, cron_file
    ))


def send_error_email(error, some_env):
    run_management_command(
        "error_emailer '{}'".format(
            error
        ),
        some_env
    )


@task
def copy_backup(branch_name):
    current_env = Env(branch_name)
    private_settings = get_private_settings()
    env.host_string = private_settings["host_string"]
    env.password = private_settings["password"]

    if not os.path.isfile(current_env.backup_name):
        send_error_email(
            "unable to find backup {}".format(
                current_env.backup_name
            ),
            current_env
        )
    else:
        with settings(warn_only=True):
            failed = put(
                local_path=current_env.backup_name,
                remote_path=current_env.backup_name
            ).failed

        if failed:
            send_error_email(
                "unable to copy backup {}".format(
                    current_env.backup_name
                ),
                current_env
            )


def get_private_settings():
    if not os.path.isfile(PRIVATE_SETTINGS):
        raise ValueError(
            "unable to find additional settings at {}".format(
                PRIVATE_SETTINGS
            )
        )

    with open(PRIVATE_SETTINGS) as privado:
        result = json.load(privado)
        err_template = "we require {} in your private settings"
        if "db_password" not in result:
            raise ValueError(err_template.format("a db password"))
        if "additional_settings" not in result:
            raise ValueError(err_template.format(
                "an additional_settings dict (even if its empty)"
            ))
        if "proxy" not in result:
            raise ValueError(err_template.format("proxy variable"))
        if "host_string" not in result:
            e = "we host string to be set, this should be 127.0.0.1 on test, \
or the address you want to sync to on prod in your private settings"
            raise ValueError(e)

    return result


@task
def clone_branch(branch_name):
    branch_env = Env(branch_name)
    local(
        "git clone -b {0} {1} {2}".format(
            branch_name,
            GIT_URL,
            branch_env.project_directory
        )
    )


@task
def create_private_settings():
    with open(PRIVATE_SETTINGS, "w") as privado:
        json.dump(
            dict(
                proxy="",
                db_password="",
                host_string="",
                additional_settings={}
            ),
            privado,
            indent=4
        )


@task
def create_empty_env(new_branch):
    _deploy(new_branch)


def _deploy(new_branch, backup_name=None):
    if backup_name and not os.path.isfile(backup_name):
        raise ValueError("unable to find backup {}".format(backup_name))

    # the new env that is going to be live
    new_env = Env(new_branch)

    # the private settings
    private_settings = get_private_settings()
    env.host_string = private_settings["host_string"]

    # Setup environment
    pip_create_virtual_env(new_env)
    pip_set_project_directory(new_env)
    pip_install_requirements(new_env, private_settings["proxy"])

    # create a database
    postgres_create_database(new_env)

    # load in a backup
    if backup_name:
        postgres_load_database(backup_name, new_env)

    # symlink the nginx conf
    services_symlink_nginx(new_env)

    # symlink the upstart conf
    services_symlink_upstart(new_env)

    # create the local settings used by the django app
    services_create_local_settings(new_env, private_settings)

    services_create_gunicorn_conf(new_env)
    services_create_upstart_conf(new_env)

    # django setup
    run_management_command("collectstatic --noinput", new_env)
    run_management_command("migrate", new_env)
    run_management_command("load_lookup_lists", new_env)


def infer_current_branch():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    project_beginning = Env('').project_directory

    if not current_dir.startswith(project_beginning):
        er_temp = 'we are in {0} but expect to be in a directory beginning \
with {1}'
        raise ValueError(er_temp.format(current_dir, project_beginning))
    return current_dir.replace(project_beginning, "")


@task
def deploy_test(backup_name):
    new_branch = infer_current_branch()
    _deploy(new_branch, backup_name)
    new_status = run_management_command("status_report", Env(new_branch))
    print("=" * 20)
    print("new environment was")
    print(new_status)
    print("=" * 20)


def validate_private_settings():
    private_settings = get_private_settings()
    if "host_string" not in private_settings:
        raise ValueError(
            'we need a host string inorder to scp data to a backup server'
        )

    if "password" not in private_settings:
        raise ValueError(
            'we need the password of the backup server inorder to scp data to a backup server'
        )


@task
def deploy_prod(old_branch):
    new_branch = infer_current_branch()
    old_env = Env(old_branch)
    new_env = Env(new_branch)

    validate_private_settings()
    dump_str = "sudo -u postgres pg_dump {0} -U postgres > {1}"
    local(dump_str.format(old_env.database_name, old_env.release_backup_name))

    cron_write_backup(new_env)
    cron_copy_backup(new_env)
    old_status = run_management_command("status_report", old_env)
    _deploy(new_branch, old_env.release_backup_name)
    new_status = run_management_command("status_report", new_env)

    print("=" * 20)
    print("old environment was")
    print(old_status)
    print("=" * 20)

    print("new environment was")
    print(new_status)
    print("=" * 20)

"""
This deals with deployment for the RFH.

Before you being make sure that in ../private_settings.json
you have
    1) the proxy address
    2) a db_password
    3) an empty dictionary called additional_settings or a dictionary
       of any other variables you want set in your local settings

Make sure the you have a back up directory which is read writeable
that is at BACKUP_DIR

Make sure you have a deployment env that has fabric available

cd {PROJECT_ROOT}
git clone https://github.com/openhealthcare/elcid-rfh.git elcidrfh-{your branch name}
cd elcidrfh-{your branch name}

e.g.
workon elcid-deployment
cd /usr/local/ohc
git clone https://github.com/openhealthcare/elcid-rfh.git elcidrfh-v0.1
cd elcidrfh-{your branch name}


Then 2 choices

deploy_test, this takes the name of the new branch and either the
the back up env and
a back up file path that it will load the environment a database back up from

deploy_prod, this will take a database back up, it will then pass this name
to deploy test. Then replace cron jobs to copy it over.

2 small tasks to look at
create_private_settings will create an empty private settings file in
the appropriate place with the fields for you to fill in

create_empty_env, takes in an environment name
creates you an empty database and a virtual env
"""

import datetime
import json
import copy
from jinja2 import Environment, FileSystemLoader
from fabric.api import local, env, settings, hide
from fabric.contrib.files import _expand_path
from fabric.operations import put
from fabric.context_managers import lcd
import os.path

env.hosts = ['127.0.0.1']
UNIX_USER = "ohc"
DB_USER = "ohc"
RELEASE_NAME = "elcidrfh-{branch}"

VIRTUAL_ENV_PATH = "/home/{usr}/.virtualenvs/{release_name}"
PROJECT_ROOT = "/usr/local/{unix_user}".format(unix_user=UNIX_USER)
PROJECT_DIRECTORY = "{project_root}/{release_name}"
BACKUP_DIR = "{project_root}/var".format(project_root=PROJECT_ROOT)

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
            release_name=self.release_name
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
    if not os.path.isdir(new_env.virtual_env_path):
        local("/usr/bin/virtualenv {}".format(new_env.virtual_env_path))
    return


def pip_install_requirements(new_env, proxy):
    pip = "{}/bin/pip".format(new_env.virtual_env_path)

    local("{} install --upgrade pip".format(pip))

    # local("{0} install --proxy {1} requirements.txt".format(pip, proxy))

    # TODO proxy switched out just for local settings
    local("{0} install -r requirements.txt".format(pip))


def pip_set_project_directory(some_env):
    local("echo '{0}' > {1}/.project".format(
        some_env.project_directory, some_env.virtual_env_path
    ))


def install_requirements(cls):
    if env.http_proxy:
        local("{0} install -r requirements.txt --proxy {1}".format(
            cls.get_pip(), env.http_proxy
        ))
    else:
        local("{0} install -r requirements.txt".format(cls.get_pip()))


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
    abs_address = os.path.join(new_env.project_directory, "etc/nginx.conf")
    if not os.path.isfile(abs_address):
        raise ValueError(
            "we expect an nginx conf to exist at {}".format(abs_address)
        )

    symlink_name = '/etc/nginx/sites-enabled/{}'.format(new_env.release_name)
    if os.path.islink(symlink_name):
        local("sudo rm {}".format(symlink_name))

    local('sudo ln -s {0} {1}'.format(abs_address, symlink_name))


def services_symlink_upstart(new_env):
    abs_address = os.path.join(new_env.project_directory, "etc/upstart.conf")
    if not os.path.isfile(abs_address):
        raise ValueError(
            "we expect an upstart conf to exist {}".format(abs_address)
        )
    symlink_name = '/etc/init/{}.conf'.format(PROJECT_NAME)
    if os.path.islink(symlink_name):
        local("sudo rm {}".format(symlink_name))

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


def services_create_gunicorn_settings(new_env):
    template = jinja_env.get_template('conf_templates/gunicorn.conf.jinja2')
    output = template.render(
        env_name=new_env.virtual_env_path
    )
    gunicorn_conf = "etc/gunicorn.conf"

    local("rm -f {}".format(gunicorn_conf))

    with open(gunicorn_conf, 'w') as f:
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
    template = jinja_env.get_template('conf_templates/cron_backup.jinja2')
    output = template.render(
        database_name=new_env.database_name,
        backup_dir=BACKUP_DIR
    )

    cron_file = "/etc/cron.d/{0}_backup".format(PROJECT_NAME)
    local("sudo rm -f {}".format(cron_file))
    local("echo '{0}' | sudo tee -a {1}".format(
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
        database_name=new_env.database_name,
        unix_user=UNIX_USER
    )
    cron_file = "/etc/cron.d/{0}_copy".format(PROJECT_NAME)
    local("sudo rm -f {}".format(cron_file))
    local("echo '{0}' | sudo tee -a {1}".format(
        output, cron_file
    ))


def copy_backup(branch_name):
    current_env = Env(branch_name)
    private_settings = get_private_settings()
    env.host_string = private_settings["host_string"]
    env.password = private_settings["password"]

    if not os.path.isfile(current_env.backup_name):
        run_management_command(
            "send error 'unable to find backup {}'".format(
                current_env.backup_name
            ),
            current_env
        )

    try:
        put(
            local_path=current_env.backup_name,
            remote_path=current_env.backup_name
        )
    except Exception as e:
        run_management_command(
            "send error 'unable to copy backup {}' with '{}'".format(
                current_env.backup_name, str(e)
            ),
            current_env
        )


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


def get_private_settings():
    if not os.path.isfile(PRIVATE_SETTINGS):
        raise ValueError(
            "unable to find additional settings at {}".format(
                PRIVATE_SETTINGS
            )
        )

    with open(PRIVATE_SETTINGS) as privado:
        result = json.load(privado)
        if "db_password" not in result:
            raise ValueError('we require a db password')
        if "additional_settings" not in result:
            e = """
            we require a dictionary of additional_settings (even if its empty)
            """.strip()
            raise ValueError(e)
        if "proxy" not in result:
            e = """
            we require a proxy variable in the private settings
            """.strip()
            raise ValueError(e)
        if "host_string" not in result:
            e = """
            we host string to be set, this should be
            127.0.0.1 on test, or the address you want to sync to on prod
            """.strip()
            raise ValueError(e)

    return result


def create_empty_env(new_branch):
    # creates an environment with an empty database
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

    # symlink the nginx conf
    services_symlink_nginx(new_env)

    # symlink the upstart conf
    services_symlink_upstart(new_env)

    # create the local settings used by the django app
    services_create_local_settings(new_env, private_settings)

    services_create_gunicorn_settings(new_env)

    # django setup
    run_management_command("collectstatic --noinput", new_env)
    run_management_command("migrate", new_env)
    run_management_command("load_lookup_lists", new_env)


def deploy_test(new_branch, backup_name=None, old_branch=None):
    # the old env that is currently live
    if (not old_branch and not backup_name) or (old_branch and backup_name):
        raise ValueError("we expect either an old branch or a back up name")

    if old_branch:
        old_env = Env(old_branch)
        # Measure old environment
        old_status = run_management_command("status_report", old_env)
        backup_name = old_env.release_backup_name
    else:
        old_status = "Unknown"

    if not os.path.isfile(backup_name):
        raise ValueError("unable to find backup {}".format(backup_name))

    # the new env that is going to be live
    new_env = Env(new_branch)

    # the private settings
    private_settings = get_private_settings()

    # Setup environment
    pip_create_virtual_env(new_env)
    pip_set_project_directory(new_env)
    pip_install_requirements(new_env, private_settings["proxy"])

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
    run_management_command("collectstatic --noinput", new_env)
    run_management_command("migrate", new_env)
    run_management_command("load_lookup_lists", new_env)
    new_status = run_management_command("status_report", new_env)

    print "=" * 20
    print "old environment was"
    print old_status
    print "=" * 20
    print "new environment was"
    print new_status
    print "=" * 20


def deploy_prod(new_branch, old_branch):
    old_env = Env(old_branch)
    new_env = Env(new_branch)
    private_settings = get_private_settings()
    if "host_string" not in private_settings:
        raise ValueError(
            'we need a host string inorder to scp data to a backup server'
        )

    if "password" not in private_settings:
        raise ValueError(
            'we need the passord of the backup server inorder to scp data to a backup server'
        )

    dump_str = "sudo -u postgres pg_dump {0} -U postgres > {1}"
    local(dump_str.format(old_env.database_name, old_env.release_backup_name))
    deploy_test(new_branch, old_branch=old_branch)
    cron_write_backup(new_env)
    cron_copy_backup(new_env)

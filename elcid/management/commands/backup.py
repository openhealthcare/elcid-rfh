"""
This backs up the database to the local disk and
to remote storage.

It also deletes old backups.
"""
import traceback
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail
import logging
import os
import subprocess
import datetime


logger = logging.getLogger('elcid')

BACKUP_DT_FORMAT = "%Y_%m_%d"


def raise_the_alarm():
    dt = datetime.date.today().strptime('%d/%m/%Y')
    msg = f"Unable to run backups for {settings.OPAL_BRAND_NAME} on {dt}"
    send_mail(
        msg,
        "",
        settings.DEFAULT_FROM_EMAIL,
        [i[1] for i in settings.ADMINS]
    )


class Command(BaseCommand):
    def clean_old_backups(self, ):
        now = datetime.datetime.now()
        dates = []
        for i in range(3):
            dates.append(
                (now - datetime.timedelta(i)).strftime(BACKUP_DT_FORMAT)
            )
        for f in os.listdir(self.backup_dirctory):
            if f.startswith("back"):
                if f.endswith("sql") or f.endswith("sql.gz"):
                    if not any(i for i in dates if i in f):
                        os.remove(os.path.join(self.backup_dirctory, f))

    def get_backup_name(self, some_dt):
        dt_formatted = some_dt.strtime("%Y_%m_%d")
        return f"back.{self.db_name}.{dt_formatted}.sql.gz"

    def dump_database(self, backup_name):
        backup_path = os.path.join(self.backup_directory, backup_name)
        cmd = f"pg_dump {self.db_name} -U {self.db_user} | gzip > {backup_path}"
        subprocess.call(cmd)

    def copy_backup(self, backup_name):
        backup_path = os.path.join(self.v.backup_dirctory, backup_name)
        cmd = " ".join([
            f"smbclient '{settings.BACKUP_STORAGE_ADDRESS}'",
            f"{settings.BACKUP_STORAGE_PASSWORD}",
            f"-U {settings.BACKUP_STORAGE_USERNAME} -I {settings.BACKUP_STORAGE_IP} -D",
            f"{settings.BACKUP_STORAGE_DIRECTORY} -c 'put {backup_path} {backup_name}'"
        ])
        subprocess.call(cmd)

    def backup(self):
        bu_name = self.get_backup_name(datetime.date.today())
        self.dump_database(bu_name)
        self.clean_old_backups(bu_name)

    def handle(self, *args, **options):
        try:
            self.db_name = settings.DATABASES['default']['NAME']
            self.db_user = settings.DATABASES['default']['USER']
            self.backup_dirctory = settings.BACKUP_DIRECTORY
            self.backup()
        except Exception as e:
            raise_the_alarm()
            logger.info(f'Unable to run backups because of {e}')
            logger.info(traceback.format_exc())

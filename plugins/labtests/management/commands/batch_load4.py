from django.core.management.base import BaseCommand
from django.core.management import call_command
from elcid.utils import timing
import csv
import os
import sys
import subprocess

LABTEST_CSV = "lab_tests.csv"
OBSERVATIONS_CSV = "observations.csv"


INSERT_LAB_TESTS = """
BEGIN;
CREATE TEMP TABLE tmp_lab_load (LIKE labtests_labtest)
ON COMMIT DROP;

ALTER TABLE tmp_lab_load DROP COLUMN id;

CREATE TEMP TABLE tmp_lab_obs (
  LIKE labtests_observation including all,
  patient_id int,
  lab_number text,
  test_name text
) ON COMMIT DROP;

ALTER TABLE tmp_lab_obs DROP COLUMN id;
ALTER TABLE tmp_lab_obs DROP COLUMN test_id;

COPY tmp_lab_load ({lab_columns}) FROM '{labtest_csv}'
DELIMITER ',' CSV HEADER;

COPY tmp_lab_obs ({csv_obs_columns}) FROM '{observations_csv}'
DELIMITER ',' CSV HEADER;

DELETE FROM labtests_labtest WHERE id IN
(
    SELECT lt.id FROM labtests_labtest lt INNER JOIN tmp_lab_load tmp_lab
    ON
    lt.test_name = tmp_lab.test_name AND
    lt.lab_number = tmp_lab.lab_number AND
    lt.patient_id = tmp_lab.patient_id
);

INSERT INTO labtests_labtest({lab_columns})
SELECT {lab_columns}
FROM tmp_lab_load;

INSERT INTO labtests_observation(test_id, {obs_table_columns})
(
SELECT lt.id, {obs_relations}
FROM labtests_labtest lt INNER JOIN tmp_lab_obs tmp_obs
ON lt.patient_id = tmp_obs.patient_id
AND lt.lab_number = tmp_obs.lab_number
);

END;
"""

@timing
def call_db_command(sql):
    """
    Calls a command on our database via psql
    """
    process = subprocess.Popen(
        ['psql', '--echo-all', '-d', 'merge_testing', '-c', f"{sql}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
    )
    while True:
        nextline = process.stdout.read()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(nextline)
        sys.stdout.flush()



def get_columns(file_name):
    with open(file_name) as f:
        reader = csv.reader(f)
        file_names = next(reader)
    return file_names


class Command(BaseCommand):
    @timing
    def handle(self, *args, **options):
        call_command('save_lab_test_csv')
        pwd = os.getcwd()
        csv_obs_columns = get_columns(OBSERVATIONS_CSV)
        obs_table_columns = [
            i for i in csv_obs_columns if i not in set(["patient_id", "lab_number", "test_name"])
        ]

        cmd = INSERT_LAB_TESTS.format(
            lab_columns=", ".join(get_columns(LABTEST_CSV)),
            labtest_csv=os.path.join(pwd, LABTEST_CSV),
            csv_obs_columns=", ".join(csv_obs_columns),
            observations_csv=os.path.join(pwd, OBSERVATIONS_CSV),
            obs_table_columns=", ".join(obs_table_columns),
            obs_relations=", ".join([f"tmp_obs.{i}" for i in obs_table_columns]),
        )
        call_db_command(cmd)

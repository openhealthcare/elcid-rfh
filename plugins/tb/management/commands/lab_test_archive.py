"""
Management command that tracks tb tests
"""
from collections import defaultdict
import datetime
import json
from opal.core.serialization import _temporal_thing_to_string
from django.core.management.base import BaseCommand
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from django.utils import timezone

FILE_NAME = "lab_test_archive.json"

Q_TB_OBS_SINCE = """
SELECT * FROM tQuest.Pathology_Result_View
WHERE OBX_exam_code_Text IN
(
'TB PCR TEST',
'AFB : CULTURE',
'AFB : EARLY MORN. URINE',
'AFB BLOOD CULTURE',
'BLOOD CULTURE'
)
and date_inserted > @since
"""


class hashabledict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


def update_file_from_qs(result, existing_dict):
    for r in result:
        test_name = r["OBR_exam_code_Text"]
        lab_number = r["Result_ID"]
        existing_dict[test_name][lab_number].add(hashabledict(r))

    to_save = defaultdict(lambda: defaultdict(list))
    for test_name, lab_number_to_rows in existing_dict.items():
        for lab_number, rows in lab_number_to_rows.items():
            to_save[test_name][lab_number] = []
            for row in list(rows):
                s_row = {k: _temporal_thing_to_string(v) for k, v in row.items()}
                to_save[test_name][lab_number].append(s_row)

    with open(FILE_NAME, "w") as f:
        json.dump(to_save, f)


def get_dict_from_file():
    with open(FILE_NAME) as a:
        existing_dict = json.load(a)
    result = defaultdict(lambda: defaultdict(set))
    for test_name, lab_number_to_rows in existing_dict.items():
        for lab_number, rows in lab_number_to_rows.items():
            for row in rows:
                result[test_name][lab_number].add(hashabledict(row))
    return result


def query(since):
    api = ProdAPI()
    return api.execute_trust_query(Q_TB_OBS_SINCE, params={
        "since": since
    })


def create_test_archive():
    since = timezone.now() - datetime.timedelta(30)
    to_save = defaultdict(lambda: defaultdict(set))
    update_file_from_qs(query(since), to_save)


def update():
    since = timezone.now() - datetime.timedelta(3)
    to_save = defaultdict(lambda: defaultdict(set))
    update_file_from_qs(query(since), to_save)


class Command(BaseCommand):
    def handle(self, *args, **options):
        update()

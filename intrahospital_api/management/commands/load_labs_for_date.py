"""
Management command to deal with gaps in the lab test feed by reloading specific days

Example usage:

python manage.py load_labs_for_date 22/12/1922
"""
import collections
import datetime

from django.core.management.base import BaseCommand

from elcid.utils import find_patient_from_mrn
from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from intrahospital_api.apis.prod_api import PathologyRow
from intrahospital_api.management.commands.batch_load2 import update_patient


LABS_FOR_DAY_QUERY = """
SELECT * FROM tQuest.Pathology_Result_view
WHERE
date_inserted >= @start
AND
date_inserted < @end
ORDER BY Patient_Number, date_inserted DESC;
"""

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('date', nargs='+')

    def handle(self, *args, **kwargs):
        date = kwargs.get('date')[0]
        start = datetime.datetime.strptime(date, '%d/%m/%Y')
        end = start + datetime.timedelta(days=1)

        api = ProdAPI()
        result = api.execute_trust_query(
            LABS_FOR_DAY_QUERY,
            params={'start': start, 'end': end}
        )
        rows = [PathologyRow(r) for r in result]

        labs_by_mrn = collections.defaultdict(list)
        for row in rows:
            labs_by_mrn[row.get_hospital_number()].append(row)

        data = []

        for mrn, rows in labs_by_mrn.items():
            patient = find_patient_from_mrn(mrn)
            if patient is None:
                continue
            else:
                demographics = rows[0].get_demographics_dict()
                labs = api.cast_rows_to_lab_test(rows)
                data.append(
                    {
                        'lab_tests'   : labs,
                        'patient'     : patient
                    }
                )

        for item in data:
            update_patient(data['patient'], data['lab_tests'])

        return

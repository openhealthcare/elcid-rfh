"""
Data exports for the research plugin
"""
import csv

from plugins.labtests.constants import WITHPATH_DEPATMENT_MAPPING as WINPATH_DEPARTMENT_MAPPING
from plugins.labtests.models import LabTest

MICRO_ID = {v: k for k, v in WINPATH_DEPARTMENT_MAPPING.items()}['Microbiology']

def write_micro_csv(patients, file_handle):
    """
    Given an iterable of PATIENTS and a FILE_HANDLE to write to,
    write a CSV of micro results for these patients.
    """
    writer = csv.writer(file_handle)
    writer.writerow([
        'study_id', 'datetime_ordered', 'site', 'test_code', 'test_name',
        'observation_datetime', 'reported_datetime', 'name', 'value', 'units'

    ])

    for patient in patients:
        print(f"Patient {patient.id}")
        labs = LabTest.objects.filter(
            patient=patient#, department_int=MICRO_ID
        ).prefetch_related('observation_set')

        for lab in labs:
            start = [
                patient.id, lab.datetime_ordered, lab.site, lab.test_code, lab.test_name
            ]

            for observation in lab.observation_set.all():
                end = [
                    observation.observation_datetime, observation.reported_datetime,
                    observation.observation_name, observation.observation_value,
                    observation.units
                ]
                row = start + end
                writer.writerow(row)

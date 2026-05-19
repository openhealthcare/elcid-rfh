"""
Custom study definition for Research plugin

This is a hook to enable custom downloads / data collection / display
"""
import collections
import csv
import datetime
import os
import shutil
import tempfile

from django.http import HttpResponse

from plugins.research import models


ExportFile = collections.namedtuple(
    'ExportFile',
    ('data', 'headers', 'filename')
)

def serialise_studies_for_patient(patient):
    """
    Given a PATIENT, return a serialised version of their studies
    for use in Angular land
    """
    studies = []
    for participation in models.StudyParticipant.objects.filter(patient=patient):
        study = participation.study

        studies.append({
            'name': study.name,
            'id'  : study.id
        })

    return studies

def create_zipfile_from_dicts(*args):
    """
    Given *ARGS of ExportFile objects, turn them into a dictionary
    of CSVs

    Return a path to a zipfile in a tempporary directory
    """
    # Make a throwaway directory with pre-zipped fiels
    with tempfile.TemporaryDirectory() as data_parent_dir:
        zipfolder = f"{datetime.date.today()}"
        data_dir = os.path.join(data_parent_dir, zipfolder)
        os.mkdir(data_dir)

        for output_file in args:
            filepath = os.path.join(data_dir, output_file.filename)
            with open(filepath, 'w') as fh:
                writer = csv.writer(fh)
                writer.writerow(output_file.headers)
                for line in output_file.data:
                    print(line)
                    writer.writerow(line)

        # this directory survives this function
        zip_dir = tempfile.mkdtemp()
        target = os.path.join(zip_dir, 'research_extract')
        archive_name = os.path.join(
            zip_dir, shutil.make_archive(target, 'zip', data_dir)
        )

    return archive_name



class StudyDefaults():
    """
    A base class to override
    """
    template_name = None

    @classmethod
    def download(klass, study):
        """
        This is the default study data download.

        Given a STUDY return an HTTPResponse that contains
        the study download
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f"attachment; filename={study.name}.csv"

        writer = csv.writer(response)
        writer.writerow(['StudyID', 'Sex', 'DOB'])

        for participant in study.get_participants():

            demographics = participant.patient.demographics()
            writer.writerow([participant.get_participant_number(), demographics.sex, demographics.date_of_birth])

        return response


class TBCustomStudy(StudyDefaults):
    """
    Example custom study
    """
    study_name = 'TB Example Study'
    template_name = 'custom_studies/tb_example.html'

    @classmethod
    def download(klass, study):
        """
        Add TB Diagnosis and tests to the download.

        Create
        """
        patient_data = []
        lab_data = []

        for participant in study.get_participants():

            participant_id = participant.get_participant_number()

            diagnosis = ''

            tb_episode = participant.patient.episode_set.filter(category_name='TB')
            if tb_episode.count() > 0:
                primary_diagnosis = tb_episode[0].diagnosis_set.filter(category='primary')
                if primary_diagnosis.count() > 0:
                    diagnosis = primary_diagnosis[0].condition

            participant_data = [
                participant_id,
                diagnosis
            ]
            patient_data.append(participant_data)

            #TODO - write properly
            tests = [
                participant_id, 'TBPCR', 'tb', '+ve', '1/12/1999'
            ]
            lab_data.append(tests)

        patient_headers = ['StudyID', 'TBDiagnosis']
        basic = ExportFile(patient_data, patient_headers, 'patients.csv')

        lab_headers = ['StudyID', 'TestName', 'LineName', 'Value', 'Timestamp']
        tb_tests = ExportFile(lab_data, lab_headers, 'labs.csv')

        archive_name = create_zipfile_from_dicts(basic, tb_tests)

        response = HttpResponse(open(archive_name, 'rb').read(), content_type='text/zip')
        response['Content-Disposition'] = f"attachment; filename={study.name}.zip"

        return response


STUDY_OVERRIDES = [
    TBCustomStudy
]

def get_study_class(name):
    """
    Given the name of a study, return the appropriate study
    class for it
    """
    for klass in STUDY_OVERRIDES:
        if klass.study_name == name:
            return klass

    return StudyDefaults

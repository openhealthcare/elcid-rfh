"""
Model definition for Elcid research plugin
"""
from django.db import models
from opal.core.fields import enum
from opal.models import Patient


class Study(models.Model):
    """
    Defines a research study.
    """
    STATES = enum('OPEN', 'CLOSED')

    created  = models.DateTimeField(auto_now_add=True)
    name     = models.TextField(blank=True, null=True)
    archived = models.BooleanField(default=False)
    state    = models.TextField(choices=STATES, default='OPEN')

    def get_absolute_url(self):
        """
        Return the URL for this study
        """
        return f"/#/research/study/{self.id}/"

    def is_open(self):
        return self.state == 'OPEN'

    def is_closed(self):
        return self.state == 'CLOSED'

    def add_participants(self, patients):
        """
        Given a list of PATIENTS, add them to this study.
        """
        for patient in patients:
            StudyParticipant.objects.get_or_create(study=self, patient=patient)
        return

    def get_participants(self):
        """
        Return an iterable of participants in this study
        """
        return [p for p in StudyParticipant.objects.filter(study=self)]

    def close_study(self):
        """
        Change the state of this study to CLOSED
        """
        self.state = 'CLOSED'
        self.save()


class StudyParticipant(models.Model):
    """
    Designates a patient as being part of a study
    """
    added = models.DateTimeField(auto_now_add=True)
    study = models.ForeignKey(
        Study, on_delete=models.CASCADE, related_name='study_participant')
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='study_participant')

    def get_participant_number(self):
        """
        Return the UID for this patient in this study
        """
        study_id = 700 + self.study_id
        # Not actually the patient ID so we can avoid leaking Elcid number
        patient_id = 900 + self.id
        return f"{study_id}{patient_id}"

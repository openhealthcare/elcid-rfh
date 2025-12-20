"""
Model definition for Elcid research plugin
"""
from django.db import models
from opal.models import Patient


class Study(models.Model):
    """
    Defines a research study.
    """
    created  = models.DateTimeField(auto_now_add=True)
    name     = models.TextField(blank=True, null=True)
    archived = models.BooleanField(default=False)

    def get_absolute_url(self):
        """
        Return the URL for this study
        """
        return f"/#/research/study/{self.id}/"


class StudyParticipant(models.Model):
    """
    Designates a patient as being part of a study
    """
    study = models.ForeignKey(
        Study, on_delete=models.CASCADE, related_name='study_participant')
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='study_participant')

    def get_participant_number(self):
        """
        Return the UID for this patient in this study
        """
        study_id = 700 + self.study_id
        patient_id = 900 + self.id
        return f"{study_id}{patient_id}"

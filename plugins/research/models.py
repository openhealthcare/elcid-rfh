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


class StudyParticipant(models.Model):
    """
    Designates a patient as being part of a study
    """
#    TODO: Auto add now added timestamp
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

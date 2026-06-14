"""
Model definition for Elcid research plugin
"""
from django.db import models
from opal.core.fields import enum
from opal.models import Patient, EpisodeSubrecord, User


class Study(models.Model):
    """
    Defines a research study.
    """
    STATES = enum('OPEN', 'CLOSED')

    created  = models.DateTimeField(auto_now_add=True)
    name     = models.TextField(blank=True, null=True)
    archived = models.BooleanField(default=False)
    state    = models.TextField(choices=STATES, default='OPEN')
    users    = models.ManyToManyField(User, blank=True)

    class Meta:
        verbose_name_plural = "studies"

    def __str__(self):
        return f"Study: {self.name}"

    def get_absolute_url(self):
        """
        Return the URL for this study
        """
        return f"/#/research/study/{self.id}/"

    def is_open(self):
        return self.state == 'OPEN'

    def is_closed(self):
        return self.state == 'CLOSED'

    def visible_to_user(self, user):
        """
        Predicate function to determine if this study is visible
        to USER
        """
        if user.is_superuser:
            return True
        if self in user.study_set.all():
            return True
        return False

    def add_participants(self, patients):
        """
        Given a list of PATIENTS, add them to this study.
        """
        for patient in patients:
            StudyParticipant.objects.get_or_create(study=self, patient=patient)
            episode = patient.episode_set.get_or_create(category_name='Research')
        return

    def get_participants(self):
        """
        Return an iterable of participants in this study
        """
        return [p for p in StudyParticipant.objects.filter(study=self, removed=False)]

    def get_removed_participants(self):
        """
        Return an iterable of removed participants in this study
        """
        return [p for p in StudyParticipant.objects.filter(study=self, removed=True)]

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
    added             = models.DateTimeField(auto_now_add=True)
    study             = models.ForeignKey(
        Study, on_delete=models.CASCADE, related_name='study_participant')
    patient           = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='study_participant')
    removed           = models.BooleanField(default=False)
    removal_reason    = models.TextField(blank=True, null=True)
    removal_timestamp = models.DateTimeField(blank=True, null=True)

    def get_participant_number(self):
        """
        Return the UID for this patient in this study
        """
        study_id = 700 + self.study_id
        # Not actually the patient ID so we can avoid leaking Elcid number
        patient_id = 900 + self.id
        return f"{study_id}{patient_id}"

    def get_research_detail_view_url(self):
        """
        Return the URL for the detail view for this patient - the research
        episode if it exists, the patient if not.
        """
        print('HERE')
        episode = self.patient.episode_set.filter(category_name="Research")
        print(episode)
        url_base = f"/#/patient/{self.patient.id}"

        if episode:
            return url_base + f"/{episode[0].id}"

        return url_base


class ResearchNote(EpisodeSubrecord):
    """
    Internal admin notes for a patient on a specific study
    """
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name='study_note')
    when  = models.DateTimeField(blank=True, null=True)
    note  = models.TextField(blank=True, null=True)

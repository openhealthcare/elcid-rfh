"""
Models for the elCID IPC plugin
"""
import datetime

from django.db import models
from django.utils import timezone
from opal.core.fields import enum
from opal.models import EpisodeSubrecord

from plugins.labtests import models as lab_test_models

from plugins.ipc.episode_categories import IPCEpisode


class InfectionAlert(EpisodeSubrecord):
    """
    An individual alert concerning a case of an infection managed
    by the Infection Prevention & Control team.

    Instances of this subrecord are created by background processes
    filtering incoming lab data, and only ever edited by users.
    """
    _category = IPCEpisode
    _icon = 'fa fa-exclamation-triangle'

    MRSA  = 'MRSA'
    CPE   = 'CPE'
    CDIFF = 'DIFF'
    TB    = 'TB'
    VRE   = 'VRE'

    CATEGORY_CHOICES = enum(
        MRSA,
        CPE,
        CDIFF,
        TB,
        VRE
    )

    # Set automatically by processing of lab data
    trigger_datetime = models.DateTimeField(blank=True)
    lab_test         = models.ForeignKey(
        lab_test_models.LabTest, on_delete=models.SET_NULL, blank=True, null=True)
    category         = models.CharField(max_length=255, choices=CATEGORY_CHOICES)

    seen             = models.BooleanField(default=False)
    comments         = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-trigger_datetime']

    def historic(self):
        "Returns true if > 6m old"
        diff = timezone.now() - self.trigger_datetime
        if diff  > datetime.timedelta(days=6*30):
            return True
        return False

"""
Admin interfaces for our observations plugin
"""
from django.contrib import admin

import reversion

from plugins.obs import models

# class ObservationAdmin(reversion.VersionAdmin):
#     pass

# admin.site.register(models.Observation, ObservationAdmin)

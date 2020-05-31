"""
Admin for elCID models
"""
from django.contrib import admin
from reversion.admin import VersionAdmin

from elcid.models import BloodCultureIsolate


admin.site.register(BloodCultureIsolate, VersionAdmin)

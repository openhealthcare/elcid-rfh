"""
Register ICU wards in the admin
"""
from django.contrib import admin
from reversion.admin import VersionAdmin

from plugins.icu.models import ICUWard, ICUHandoverLocation

admin.site.register(ICUHandoverLocation, VersionAdmin)
admin.site.register(ICUWard, VersionAdmin)

from django.contrib import admin
from elcid.models import BloodCultureIsolate
from reversion.admin import VersionAdmin

admin.site.register(BloodCultureIsolate, VersionAdmin)
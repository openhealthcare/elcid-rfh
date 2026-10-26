"""
Admin site additions for the Elcid RNOH module
"""
from django.contrib import admin

from plugins.rnoh.models import RNOHUsefulNumbers

class NumberAdmin(admin.ModelAdmin):
    model = RNOHUsefulNumbers

admin.site.register(RNOHUsefulNumbers, NumberAdmin)

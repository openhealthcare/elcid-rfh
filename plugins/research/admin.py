"""
Admin site for Elcid Research plugin
"""
from django.contrib import admin
from opal.models import User

from plugins.research.models import Study


class StudyAdmin(admin.ModelAdmin):
    model = Study
    filter_horizontal = ('users', )

admin.site.register(Study, StudyAdmin)

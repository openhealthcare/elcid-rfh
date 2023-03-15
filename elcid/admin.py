"""
Admin for elCID models
"""
from django.contrib.auth.models import User
from django.contrib import admin
from reversion.admin import VersionAdmin
from opal import admin as opal_admin
from django.contrib.auth.admin import UserAdmin
from elcid import forms

from elcid.models import BloodCultureIsolate


admin.site.unregister(User)


class ElcidUserAdmin(opal_admin.UserProfileAdmin):
    form = forms.ElcidUserAdminChangeForm
    add_form = forms.ElcidUserAdminCreationForm

admin.site.register(User, ElcidUserAdmin)


admin.site.register(BloodCultureIsolate, VersionAdmin)

"""
Admin for elCID models
"""
from django import forms as django_forms
from django.contrib.auth.models import User
from django.contrib import admin
from reversion.admin import VersionAdmin
from opal import admin as opal_admin
from django.contrib.auth import forms as user_forms
from django.contrib.auth.models import User

from elcid.models import BloodCultureIsolate, BloodCultureListMetadata


admin.site.unregister(User)


class ElcidUserAdminCreationForm(user_forms.UserCreationForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if len(email) == 0:
            return email
        existing_user = User.objects.filter(
            email=email
        ).first()
        if existing_user is not None:
            raise django_forms.ValidationError(
                f"Email is currently in use by {existing_user.username}"
            )
        return email


class ElcidUserAdminChangeForm(user_forms.UserChangeForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if len(email) == 0:
            return email
        existing_user = User.objects.exclude(
            id=self.instance.id
        ).filter(
            email=email
        ).first()
        if existing_user:
            raise django_forms.ValidationError(
                f"Email is currently in use by {existing_user.username}"
            )
        return email


class ElcidUserAdmin(opal_admin.UserProfileAdmin):
    form = ElcidUserAdminChangeForm
    add_form = ElcidUserAdminCreationForm


class BloodCultureMetadataAdmin(VersionAdmin):
    list_display = [
        'episode',
        'patient',
        'active',
        'date_added',
        'added_by',
        'date_removed',
        'removed_by',
        'validation_overridden',
        'override_justification'
    ]

    list_filter = [
        'active',
        'validation_overridden'
    ]

    def patient(self, obj):
        return obj.episode.patient.demographics().name

admin.site.register(User, ElcidUserAdmin)


admin.site.register(BloodCultureIsolate, VersionAdmin)

admin.site.register(BloodCultureListMetadata, BloodCultureMetadataAdmin)

"""
Forms for eLCID
"""
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth import forms as user_forms

class BulkCreateUsersForm(forms.Form):
    """
    Form for uploading a CSV of users to add.
    """
    users = forms.FileField()


class ElcidUserAdminCreationForm(user_forms.UserCreationForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if len(email) == 0:
            return email
        existing_user = User.objects.filter(
            email=email
        ).first()
        if existing_user is not None:
            raise forms.ValidationError(
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
            raise forms.ValidationError(
                f"Email is currently in use by {existing_user.username}"
            )
        return email

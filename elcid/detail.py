"""
Custom Detail view for elCID
"""
from opal.core import detail
from intrahospital_api import constants


class Result(detail.PatientDetailView):
    display_name = "Test Results"
    order        = 5
    template     = "detail/result.html"

    @classmethod
    def visible_to(klass, user):
        # The excluded roles are hardcoded in ElcidPostLoginCtrl
        return True

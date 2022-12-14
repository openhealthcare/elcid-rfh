"""
Custom Detail view for elCID
"""
from opal.core import detail
from intrahospital_api import constants


class Result(detail.PatientDetailView):
    display_name = "Test Results"
    order        = 5
    template     = "detail/result.html"

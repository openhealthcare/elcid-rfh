"""
Custom Detail view to display admissions
"""
from opal.core import detail


class AdmissionDetailView(detail.PatientDetailView):
    display_name = "Admissions"
    order        = 9
    template     = "detail/admissions.html"

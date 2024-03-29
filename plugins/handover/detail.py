"""
Custom detail view to display Handover details
"""
from opal.core import detail


class AMTHandoverDetailView(detail.PatientDetailView):
    display_name = 'AMT Handover'
    order        = 60
    template     = 'detail/amt_handover.html'


class NursingHandoverDetailView(detail.PatientDetailView):
    display_name = 'Nursing Handover'
    order        = 80
    template     = 'detail/nursing_handover.html'

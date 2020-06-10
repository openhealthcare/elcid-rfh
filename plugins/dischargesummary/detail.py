"""
Custom detail view to display discharge summaries
"""
from opal.core import detail


class DischargeSummaryDetailView(detail.PatientDetailView):
    display_name = 'Discharge Summaries'
    order        = 30
    template     = 'detail/discharges.html'

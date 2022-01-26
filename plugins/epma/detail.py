"""
Custom Detail view to display epma
"""
from opal.core import detail


class EPMADetailView(detail.PatientDetailView):
    display_name = 'EPMA'
    order        = 21
    template     = 'detail/epma.html'

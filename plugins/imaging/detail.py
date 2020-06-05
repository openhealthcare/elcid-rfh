"""
Custom Detail view to display imaging
"""
from opal.core import detail


class ImagingDetailView(detail.PatientDetailView):
    display_name = 'Imaging'
    order        = 21
    template     = 'detail/imaging.html'

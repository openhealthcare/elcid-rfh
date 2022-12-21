"""
Custom Detail view to display admissions
"""
from opal.core import detail
from plugins.ipc import constants as ipc_constants


class AdmissionDetailView(detail.PatientDetailView):
    display_name = "Admissions"
    order        = 9
    template     = "detail/admissions.html"


class LocationHistoryView(detail.PatientDetailView):
    display_name = "Location History"
    order        = 10
    template     = "detail/location_history.html"

    @classmethod
    def visible_to(klass, user):
        if user.is_superuser:
            return True
        ipc_user = user.profile.roles.filter(
            name=ipc_constants.IPC_ROLE
        ).exists()
        if ipc_user:
            return True
        return False

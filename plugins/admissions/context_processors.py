"""
Context processors for the elCID IPC module
"""

def hospitals(request):
    """
    Context processor that provides a list of distinct currently active
    hospital sites and hospital site codes as defined by the upstream
    bed status data
    """
    if not request.user or not request.user.is_active:
        return {}

    from plugins.admissions.models import BedStatus
    hospitals = BedStatus.objects.values_list(
        'hospital_site_description', 'hospital_site_code').distinct().order_by('hospital_site_code')

    return {'hospitals': hospitals}

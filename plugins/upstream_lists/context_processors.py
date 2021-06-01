"""
Context Processors for Upstream Lists
"""
from plugins.icu.models import current_icu_patients


def upstream_lists(request):
    from plugins.icu.models import ICUHandoverLocation
    wards = ICUHandoverLocation.objects.filter(
        patient__in=current_icu_patients()
    ).values_list('ward', flat=True).distinct()

    return {'upstream_lists': [
        (f'#/list/upstream/{ward}', f'Auto ICU {ward}') for ward in wards
    ]}

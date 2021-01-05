"""
Context Processors for Upstream Lists
"""

def upstream_lists(request):
    from plugins.icu.models import ICUHandoverLocation
    wards = ICUHandoverLocation.objects.all().values_list('ward', flat=True).distinct()

    return {'upstream_lists': [
        (f'#/list/upstream/{ward}', f'Auto ICU {ward}') for ward in wards
    ]}

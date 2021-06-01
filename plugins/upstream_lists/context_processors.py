"""
Context Processors for Upstream Lists
"""
from plugins.icu.models import current_icu_patients
from django.utils.functional import SimpleLazyObject


def upstream_lists(request):
    def get_icu_wards():
        from plugins.icu.models import ICUHandoverLocation
        wards = ICUHandoverLocation.objects.filter(
            patient__in=current_icu_patients()
        ).values_list('ward', flat=True).distinct()
        return [
            (f'#/list/upstream/{ward}', f'Auto ICU {ward}') for ward in wards
        ]
    # Wrap it in a simple lazy object so that if the upstream_lists
    # are not referenced we don't do the calculation
    return {'upstream_lists': SimpleLazyObject(get_icu_wards)}

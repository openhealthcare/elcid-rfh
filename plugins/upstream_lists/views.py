"""
Views for the upstream lists plugin
"""
from django.views.generic import TemplateView
from opal.core.patient_lists import PatientList


class UpstreamListTemplateView(TemplateView):
    template_name = 'upstream_lists/episode_list.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['patient_list'] = {
            'display_name': f"Auto ICU {kwargs['slug']}",
            'is_read_only': True
        }
        ctx['lists'] = list(PatientList.for_user(self.request.user))
        return ctx

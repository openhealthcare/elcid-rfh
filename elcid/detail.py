from opal.core import detail
from django.conf import settings


class Result(detail.PatientDetailView):
    display_name = "Test Results"
    order = 5
    template = "detail/result.html"

    @classmethod
    def visible_to(klass, user):
        if user.is_superuser:
            return True
        return settings.GLOSS_ENABLED


class HorizontalResult(detail.PatientDetailView):
    display_name = "Horizontal Results"
    order = 5
    template = "detail/horizontal_result.html"

    @classmethod
    def visible_to(klass, user):
        if user.is_superuser:
            return True
        return settings.GLOSS_ENABLED


class JsonDumpView(detail.PatientDetailView):
    display_name = "Json Dump View"
    order = 5
    template = "detail/json_dump_view.html"

    @classmethod
    def visible_to(klass, user):
        if user.is_superuser:
            return True
        return settings.GLOSS_ENABLED

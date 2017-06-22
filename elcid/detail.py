from opal.core import detail


class Result(detail.PatientDetailView):
    display_name = "Test Results"
    order = 5
    template = "detail/result.html"

    @classmethod
    def visible_to(klass, user):
        if user.is_superuser:
            return True
        return False


class JsonDumpView(detail.PatientDetailView):
    display_name = "Json Dump View"
    order = 5
    template = "detail/json_dump_view.html"

    @classmethod
    def visible_to(klass, user):
        if user.is_superuser:
            return True
        return False
